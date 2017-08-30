import functools
import hashlib
import hmac
import subprocess
from base64 import b64encode
from io import BytesIO

import qrcode
from flask import abort
from flask import request
from flask import session
from flask_login import current_user
from flask_socketio import disconnect
from peewee import DoesNotExist

from home import settings
from home.core.async import run
from home.core.models import get_device, devices
from home.core.utils import random_string, method_from_name
from home.settings import BASE_URL, PUBLIC_GROUPS
from home.web.models import APIClient, Subscriber, User

try:
    VERSION = 'v' + subprocess.check_output(['git', 'describe', '--tags', 'HEAD']).decode('UTF-8')
except:
    VERSION = 'unknown'

logger = None
guest_path = ""
guest_path_qr = None


def ws_login_required(f):
    """
    Authenticate Websocket requests
    :param f: Decorated function
    :return: Function
    """

    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)

    return wrapped


def ws_optional_auth(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if current_user.is_authenticated:
            kwargs['auth'] = True
        return f(*args, **kwargs)

    return wrapped


def api_auth_required(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        try:
            if request.headers.get('X-Gogs-Signature'):
                client = APIClient.get(name='gogs-update')
                secret = bytes(client.token.encode())
                mac = hmac.new(secret, msg=request.get_data(), digestmod=hashlib.sha256)
                if not hmac.compare_digest(mac.hexdigest(), request.headers['X-Gogs-Signature']):
                    abort(403)
            else:
                client = APIClient.get(token=request.values.get('key'))
            kwargs['client'] = client
        except DoesNotExist:
            if settings.DEBUG:
                kwargs['client'] = APIClient.get()
            else:
                abort(403)
        return f(*args, **kwargs)

    return wrapped


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = random_string()
    return session['_csrf_token']


def send_to_subscribers(message):
    for subscriber in Subscriber.select():
        try:
            subscriber.push(message)
        except Exception as e:
            print("Webpusher:", str(e))


def handle_task(post, client):
    device = get_device(post.pop('device'))
    try:
        c_method, c_kwargs = device.last.pop()
    except IndexError:
        c_method, c_kwargs = None, None
    try:
        l_method, l_kwargs = device.last.pop()
    except IndexError:
        l_method, l_kwargs = None, None
    else:
        device.last.append((l_method, l_kwargs))
        device.last.append((c_method, c_kwargs))
    if post.get('method') == 'last':
        # The most recent action
        # The previous action
        method = l_method
        kwargs = l_kwargs
    else:
        print(device, device.dev, post.get('method'))
        method = method_from_name(device.dev, post.pop('method'))
        if post.get('increment'):
            kwargs = c_kwargs
            kwargs[post['increment']] += post.get('count', 1)
        elif post.get('decrement'):
            kwargs = c_kwargs
            kwargs[post['decrement']] += post.get('count', 1)
        else:
            kwargs = post
    device.last.append((method, kwargs))
    from home.web.web import app
    app.logger.info(
        "({}) Execute {} on {} with config {}".format(client.name, method.__name__, device.name, kwargs))
    if device.driver.noserialize:
        method(**kwargs)
    else:
        device.last_task = run(method, **kwargs)


def gen_guest_login():
    global guest_path, guest_path_qr
    guest_path = 'display/' + random_string()
    buf = BytesIO()
    qr = qrcode.make(BASE_URL + guest_path)
    qr.save(buf, "PNG")
    guest_path_qr = b64encode(buf.getvalue()).decode()


def get_qr():
    return guest_path_qr, guest_path


def get_widgets(user: User):
    widget_html = []
    for d in devices:
        if d.group in PUBLIC_GROUPS or d.group in user.groups or user.admin:
            try:
                widget_html.append(d.widget['html'])
            except (AttributeError, TypeError):
                pass
    return widget_html
