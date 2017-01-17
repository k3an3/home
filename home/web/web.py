import functools
import json
import subprocess
import sys

from flask import Flask, render_template, request, redirect, flash, abort, session, url_for
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_socketio import SocketIO, emit, disconnect
from pywebpush import WebPusher

import home.core.utils as utils
from home.core.models import devices, interfaces, get_device_by_key, get_action, get_device
from home.core.utils import random_string
from home.web.models import *

app = Flask(__name__)
app.secret_key = '\xff\xe3\x84\xd0\xeb\x05\x1b\x89\x17\xce\xca\xaf\xdb\x8c\x13\xc0\xca\xe4'
API_KEY = 'AIzaSyCa349yW3-oWMbYRHl21V1IgGRyM6O7PW4'
app.debug = True
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.init_app(app)

try:
    VERSION = 'v' + subprocess.check_output(['git', 'describe', '--tags', 'HEAD']).decode('UTF-8')
except:
    VERSION = 'unknown'

# TODO: remove
sys.path.append(os.path.dirname("/home/keane/dev/home/home"))


def ws_login_required(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped


@app.route('/', methods=['GET', 'POST'])
def index():
    sec = SecurityController.get()
    events = sec.events
    interface_list = []
    for i in interfaces:
        interface_list.append((i, [d for d in devices if d.driver.interface == i]))
    return render_template('index.html',
                           interfaces=interface_list,
                           devices=devices,
                           sec=sec,
                           events=events,
                           version=VERSION,
                           )


@app.route('/api/command', methods=['POST'])
def command_api():
    try:
        device = get_device_by_key(request.form.get('device'))
    except StopIteration:
        abort(403)
    sec = SecurityController.get()
    command = request.form.get('command')
    if sec.state == 'armed':
        if command == 'eventstart':
            print("EVENT START")
            sec.alert()
            SecurityEvent.create(controller=sec, device=device)
            socketio.emit('state change', {'state': sec.state}, namespace='/ws')
            for subscriber in Subscriber.select():
                try:
                    WebPusher(subscriber.to_dict()).send(
                        json.dumps({'body': "New event alert!!!"}),
                        gcm_key=API_KEY)
                except Exception as e:
                    print(str(e))
        elif command == 'eventend':
            print("EVENT END")
            try:
                event = SecurityEvent.get(controller=sec, device=device)
                event.in_progress = False
                event.save()
                # emit something here
            except SecurityEvent.DoesNotExist:
                abort(412)
    return '', 204


@socketio.on('change state', namespace='/ws')
@ws_login_required
def change_state():
    if not current_user.admin:
        disconnect()
    sec = SecurityController.get()
    if sec.state == 'disabled':
        # Set to armed
        sec.arm()
        get_action('arm').run()
    elif sec.state == 'armed':
        # Set to disabled
        sec.disable()
        get_action('disable').run()
    elif sec.state == 'alert':
        # Restore to armed
        sec.arm()
    emit('state change', {'state': sec.state}, broadcast=True)


@socketio.on('subscribe', namespace='/ws')
@ws_login_required
def subscribe(subscriber):
    s, created = Subscriber.get_or_create(
        endpoint=subscriber.get('endpoint'),
        auth=subscriber.get('keys')['auth'],
        p256dh=subscriber.get('keys')['p256dh'],
        user=current_user.id)
    if created:
        WebPusher(subscriber).send(
            json.dumps({'body': "Subscribed to push notifications!"}),
            gcm_key=API_KEY)


@socketio.on('change color', namespace='/ws')
@ws_login_required
def request_change_color(message):
    emit('push color', {"device": message['device'], "color": message['color']},
         broadcast=True)
    device = get_device(message['device'])
    device.dev.change_color(*utils.RGBfromhex(message['color']),
                            utils.num(message.get('white', 0)), message.get('bright', 100), '41'
                            )


@socketio.on('outmap', namespace="/ws")
@ws_login_required
def reset_color_preview(message):
    emit('preview reset', message['color'], broadcast=True)


@login_manager.user_loader
def user_loader(user_id):
    return User.get(username=user_id)


@app.route('/login', methods=['POST'])
def login():
    user = User.get(username=request.form.get('username'))
    if user.check_password(request.form.get('password')):
        login_user(user)
        flash('Logged in successfully.')
    return redirect(url_for('index'))


@app.route("/logout")
@login_required
def logout():
        logout_user()
        return redirect(url_for('index'))


# This hook ensures that a connection is opened to handle any queries
# generated by the request.
@app.before_request
def _db_connect():
    db.connect()


# This hook ensures that the connection is closed when we've finished
# processing the request.
@app.teardown_request
def _db_close(obj):
    if not db.is_closed():
        db.close()


@app.before_request
def csrf_protect():
    if request.method == "POST" and request.path != '/api/command':
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = random_string()
    return session['_csrf_token']


@app.after_request
def add_header(response):
    # response.headers['Content-Security-Policy'] = "connect-src 'self'"
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


app.jinja_env.globals['csrf_token'] = generate_csrf_token


if __name__ == '__main__':
    db_init()
    try:
        import eventlet
        eventlet.monkey_patch()
        print('Using eventlet')
        create_thread_func = lambda f: f
        start_thread_func = lambda f: eventlet.spawn(f)
    except ImportError:
        try:
            import gevent
            import gevent.monkey
            gevent.monkey.patch_all()
            print('Using gevent')
            create_thread_func = lambda f: gevent.Greenlet(f)
            start_thread_func = lambda t: t.start()
        except ImportError:
            import threading
            print('Using threading')
            create_thread_func = lambda f: threading.Thread(target=f)
            start_thread_func = lambda t: t.start()
    socketio.run(app, debug=True)
