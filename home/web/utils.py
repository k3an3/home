import functools
import subprocess

from flask import abort
from flask import request
from flask import session
from flask_login import current_user
from flask_socketio import disconnect
from peewee import DoesNotExist

from home.core.utils import random_string
from home.web.models import APIClient, Subscriber

try:
    VERSION = 'v' + subprocess.check_output(['git', 'describe', '--tags', 'HEAD']).decode('UTF-8')
except:
    VERSION = 'unknown'


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
            if request.is_json:
                client = APIClient.get(token=request.get_json()['secret'])
            else:
                client = APIClient.get(token=request.values.get('key'))
            kwargs['client'] = client
        except DoesNotExist:
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
