import functools
from flask import abort, request
from flask_login import login_required
from flask_socketio import join_room, emit

from home.core.models import get_device
from home.settings import DEBUG
from home.web.utils import api_auth_required
from home.web.web import socketio, app


class TrackedDevice:
    def __init__(self, id_: str):
        self.id = id_
        self.sid = None

    def cmd(self, cmd: str):
        socketio.emit('cmd', {'cmd': cmd}, namespace='/tracker', room="asdf")

    def register(self):
        socketio.emit('cmd', {'cmd': 'ls'}, namespace='/tracker', room="asdf")


@app.route('/api/tracker', methods=['POST'])
@api_auth_required
def commands(client):
    command = request.form.get('command')
    if command == 'exec':
        socketio.emit('cmd', {'cmd': request.form.get('cmd')}, namespace='/tracker', room="asdf")
    return '', 204


def ws_android_auth(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        t = get_device('android')
        t.dev.sid = request.sid
        if DEBUG:
            return f(*args, **kwargs)
        abort(403)

    return wrapped


@socketio.on('register', namespace='/tracker')
@ws_android_auth
def register(data):
    print(data['id'], "tried to register")
    join_room("asdf")
    emit('registered', 'registered')
