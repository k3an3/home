import functools
from flask import abort, request
from flask_login import login_required
from flask_socketio import join_room, emit

from home.core.models import get_device
from home.settings import DEBUG
from home.web.utils import api_auth_required, ws_login_required
from home.web.web import socketio, app


class TrackedDevice:
    def __init__(self, token: str):
        self.id = token
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


@socketio.on('exec')
@ws_login_required
def exec_cmd(data):
    emit('cmd', {'cmd': data['cmd'], 'root': data['root'], 'noroot': data['noroot']},
         namespace='/tracker', room="asdf")


# Android to Server #
@socketio.on('register', namespace='/tracker')
@ws_android_auth
def register(data):
    print(data['id'], "tried to register")
    join_room("asdf")
    emit('registered', 'registered')


@socketio.on('result', namespace='/tracker')
@ws_android_auth
def result(data):
    print('Got results', data)
    emit('results', data, namespace="/", broadcast=True)


@socketio.on('location', namespace='/tracker')
@ws_android_auth
def result(data):
    print('Got location', data)
    emit('location', data, namespace="/", broadcast=True)
