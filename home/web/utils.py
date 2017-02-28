import functools
import subprocess

from flask import session
from flask_login import current_user
from flask_socketio import disconnect

from home.core.utils import random_string

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


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = random_string()
    return session['_csrf_token']