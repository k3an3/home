import functools
import hashlib
import hmac
import subprocess
from base64 import b64encode
from io import BytesIO
from typing import List, Any

import qrcode
from flask import abort
from flask import request
from flask import session
from flask_login import current_user
from flask_socketio import disconnect
from ldap3 import Server, Connection, ALL_ATTRIBUTES
from peewee import DoesNotExist

from home.core.models import get_device, devices, actions, MultiDevice, get_device_by_uuid, devices_by_uuid
from home.core.tasks import run
from home.core.utils import random_string, method_from_name, get_groups
from home.settings import BASE_URL, LDAP_BASE_DN, LDAP_FILTER, LDAP_HOST, LDAP_PORT, LDAP_SSL, \
    LDAP_ADMIN_GROUP, DEBUG
from home.web.models import APIClient, Subscriber, User

try:
    VERSION = 'v' + subprocess.check_output(['git', 'describe', '--tags', 'HEAD']).decode('UTF-8')
except:
    VERSION = 'unknown'

logger = None
guest_path = ""
guest_path_qr = None


def ws_login_required(_f=None, has_permission: str = None, check_device: bool = False):
    """
    Authenticate Websocket requests
    :param check_device: Whether to extract device object and check user's permissions against it
    :param has_permission: String representing a permission group
    :param _f: Decorated function
    :return: Function
    """

    def decorator_ws_login(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if current_user.is_authenticated:
                if has_permission and current_user.has_permission(
                        group=has_permission):
                    return f(*args, **kwargs)
                elif check_device:
                    device = get_device(args[0]['device'].replace('-', ' '))
                    if current_user.has_permission(device):
                        kwargs['device'] = device
                        return f(*args, **kwargs)
                elif not has_permission and not check_device:
                    return f(*args, **kwargs)
            disconnect()
        return wrapped

    if _f is None:
        return decorator_ws_login
    else:
        return decorator_ws_login(_f)


def ws_optional_auth(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if current_user.is_authenticated:
            kwargs['auth'] = True
        return f(*args, **kwargs)

    return wrapped


def api_auth_required(_f=None, has_permission: str = None, check_device: bool = False):
    def decorator_api_auth(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            try:
                if request.is_json:
                    data = request.get_json()
                    kwargs['data'] = data
                    device = data.get('device')
                else:
                    device = request.values.get('device')

                if request.headers.get('X-Gogs-Signature'):
                    client = APIClient.get(name='gogs-update')
                    secret = bytes(client.token.encode())
                    mac = hmac.new(secret, msg=request.get_data(), digestmod=hashlib.sha256)
                    if not hmac.compare_digest(mac.hexdigest(), request.headers['X-Gogs-Signature']):
                        abort(403)
                elif request.headers.get('X-Auth-Token'):
                    client = APIClient.get(token=request.headers['X-Auth-Token'])
                elif request.is_json:
                    client = APIClient.get(token=data['key'])
                else:
                    client = APIClient.get(token=request.values.get('key'))

                if client:
                    kwargs['client'] = client
                    if has_permission and not client.has_permission(has_permission):
                        abort(403)
                    elif check_device:
                        device = get_device(device.replace('-', ' '))
                        if client.has_permission(device.group):
                            return f(*args, device, **kwargs)
            except DoesNotExist:
                if DEBUG:
                    kwargs['client'] = APIClient.get()
                else:
                    from home.web.web import app
                    app.logger.warning("No API client exists for the request.")
                    abort(403)
            return f(*args, **kwargs)

        return wrapped

    if _f is None:
        return decorator_api_auth
    else:
        return decorator_api_auth(_f)


def generate_csrf_token() -> str:
    if '_csrf_token' not in session:
        session['_csrf_token'] = random_string()
    return session['_csrf_token']


def send_to_subscribers(message: str, groups: List[str]) -> None:
    for subscriber in Subscriber.select():
        send = False
        if groups:
            for group in groups:
                if subscriber.user.has_permission(group=group):
                    send = True
                    break
        else:
            send = True
        if send:
            try:
                subscriber.push(message)
            except Exception as e:
                print("Webpusher:", str(e))


def handle_task(post: dict, client: APIClient) -> bool:
    try:
        device = get_device(post.pop('device').strip())
        method = method_from_name(device.dev, post.pop('method'))
    except StopIteration:
        return False
    from home.web.web import app
    if not client.has_permission(device.group):
        app.logger.warning(
            "({}) Insufficient API permissions to execute '{}' on '{}' with config {}".format(
                client.name, method.__name__, device.name, post))
        return False
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
    for d in devices.values():
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
    c = Connection(s, user=(LDAP_FILTER.format(username) + ',' + LDAP_BASE_DN), password=password)
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
                                                  'admin': LDAP_ADMIN_GROUP in r['memberOf']
                                                  })
        if created:
            app.logger.info("Created new user from LDAP: " + username)
        else:
            u.admin = LDAP_ADMIN_GROUP in r['memberOf']
            u.save()
    else:
        app.logger.info("Failed to bind with user " + LDAP_FILTER.format(username) + "," + LDAP_BASE_DN)
    c.unbind()
    return u


def filter_by_permission(user: User, objects: List[Any]):
    if user.admin:
        return objects
    return [o for o in objects if user.has_permission(o)]
