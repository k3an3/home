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
from ldap3 import Server, Connection, ALL_ATTRIBUTES
from peewee import DoesNotExist
from typing import List, Any

from home.core.async import run
from home.core.models import get_device, devices, actions, MultiDevice
from home.core.utils import random_string, method_from_name, get_groups
from home.settings import PUBLIC_GROUPS, BASE_URL, LDAP_BASE_DN, LDAP_FILTER, LDAP_HOST, LDAP_PORT, LDAP_SSL, \
    LDAP_ADMIN_GID, DEBUG
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
            if DEBUG:
                kwargs['client'] = APIClient.get()
            else:
                abort(403)
        return f(*args, **kwargs)

    return wrapped


def generate_csrf_token() -> str:
    if '_csrf_token' not in session:
        session['_csrf_token'] = random_string()
    return session['_csrf_token']


def send_to_subscribers(message: str) -> None:
    for subscriber in Subscriber.select():
        try:
            subscriber.push(message)
        except Exception as e:
            print("Webpusher:", str(e))


def handle_task(post: dict, client: APIClient) -> bool:
    device = get_device(post.pop('device').strip())
    method = method_from_name(device.dev, post.pop('method'))
    from home.web.web import app
    if not client.has_permission(device.group):
        app.logger.warning(
            "({}) Insufficient API permissions to execute '{}' on '{}' with config {}".format(
                client.name, method.__name__, device.name, post))
        return False
    device.last.append((method, post))
    app.logger.info(
        "({}) Execute '{}' on '{}' with config {}".format(client.name, method.__name__, device.name, post))
    if device.driver.noserialize or type(device) is MultiDevice:
        method(**post)
    else:
        device.last_task = run(method, **post)
    return True


def gen_guest_login() -> None:
    global guest_path, guest_path_qr
    guest_path = 'display/' + random_string()
    buf = BytesIO()
    qr = qrcode.make(BASE_URL + guest_path)
    qr.save(buf, "PNG")
    guest_path_qr = b64encode(buf.getvalue()).decode()


def get_qr() -> (str, str):
    return guest_path_qr, guest_path


def get_widgets(user: User) -> List[str]:
    widget_html = []
    for d in devices:
        if user.has_permission(d):
            try:
                widget_html.append(d.widget['html'])
            except (AttributeError, TypeError):
                pass
    return widget_html


def get_action_widgets(user: User) -> List[str]:
    widget_html = []
    groups = get_groups(actions)
    for group in groups:
        if user.has_permission(group=group):
            html = ''
            html += '<div class="widget-panel panel panel-info"><div class="panel-heading"><h3 ' \
                    'class="panel-title">{}</h3></div><div class="panel-body">'.format(group)
            html += '<div class="btn-group" role="group" aria-label="...">'
            action_html = ''
            for action in groups[group]:
                if action.button:
                    action_html += '<button class="widget btn {1}" id="{0}">{0}</button>'.format(action.name,
                                                                                                 action.button)
            html += action_html
            html += '</div></div></div>'
            if action_html:
                widget_html.append(html)
    return widget_html


def ldap_auth(username: str, password: str) -> User:
    s = Server(host=LDAP_HOST, port=LDAP_PORT, use_ssl=LDAP_SSL)
    with Connection(s, user=(LDAP_FILTER.format(username) + ',' + LDAP_BASE_DN), password=password) as c:
        u = None
        from home.web.web import app
        if c.bind():
            app.logger.info("Successful bind for user " + username)
            c.search(search_base=LDAP_BASE_DN,
                     search_filter='({})'.format(LDAP_FILTER.format(username)),
                     attributes=ALL_ATTRIBUTES)
            r = c.response[0]['attributes']
            u, created = User.get_or_create(username=username,
                                            defaults={'ldap': True,
                                                      'password': '',
                                                      'admin': r['gidnumber'] == LDAP_ADMIN_GID
                                                      })
            if created:
                app.logger.info("Created new user from LDAP: " + username)
            else:
                u.admin = r['gidnumber'] == LDAP_ADMIN_GID
                u.save()
        else:
            app.logger.info("Failed to bind with user " + LDAP_FILTER.format(username) + "," + LDAP_BASE_DN)
        return u
