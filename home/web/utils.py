import functools
import hashlib
import hmac
import subprocess

from flask import abort
from flask import request
from flask import session
from flask_login import current_user
from flask_socketio import disconnect
from peewee import DoesNotExist

from home import settings
from home.core.async import run
from home.core.models import get_device
from home.core.utils import random_string, method_from_name
from home.web.models import APIClient, Subscriber

try:
    VERSION = 'v' + subprocess.check_output(['git', 'describe', '--tags', 'HEAD']).decode('UTF-8')
except:
    VERSION = 'unknown'

logger = None


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
    if device.last_task:
        pass
        # app.logger.info(device.last_task.state)
        # device.last_task.revoke()
    if post.get('method') == 'last':
        method = device.last_method
        kwargs = device.last_kwargs
    else:
        print(device, device.dev, post.get('method'))
        method = method_from_name(device.dev, post.pop('method'))
        if post.get('increment'):
            kwargs = device.last_kwargs
            kwargs[post['increment']] += post.get('count', 1)
        elif post.get('decrement'):
            kwargs = device.last_kwargs
            kwargs[post['decrement']] += post.get('count', 1)
        else:
            kwargs = post
            device.last_method = method
            device.last_kwargs = kwargs
    from home.web.web import app
    app.logger.info(
        "({}) Execute {} on {} with config {}".format(client.name, method.__name__, device.name, kwargs))
    if device.driver.noserialize:
        method(**kwargs)
    else:
        device.last_task = run(method, **kwargs)
