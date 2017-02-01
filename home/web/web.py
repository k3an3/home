"""
web.py
~~~~~~

Flask web application for Home.
"""
import ast
import functools
import json
import subprocess
import sys

from flask import Flask, render_template, request, redirect, flash, abort, session, url_for
from flask_login import LoginManager, login_required, login_user, current_user, logout_user, fresh_login_required
from flask_socketio import SocketIO, emit, disconnect
from pywebpush import WebPusher

import home.core.parser as parser
import home.core.utils as utils
from home.core.models import devices, interfaces, get_device_by_key, get_action, get_device, actions
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


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Route for the HTML interface.
    """
    sec = SecurityController.get()
    events = sec.events
    interface_list = []
    for i in interfaces:
        interface_list.append((i, [d for d in devices if d.driver and d.driver.interface == i]))
    return render_template('index.html',
                           interfaces=interface_list,
                           devices=devices,
                           sec=sec,
                           events=events,
                           actions=actions,
                           version=VERSION,
                           )


@app.route('/api/command', methods=['POST'])
def command_api():
    """
    Command API used by devices.
    """
    try:
        key = get_device_by_key(request.form.get('key'))
    except StopIteration:
        abort(403)
    if request.form.get('device'):
        device = get_device(request.form.get('device'))
        method = utils.method_from_name(type(device.dev), request.form.get('method'))
        config = ast.literal_eval(request.form.get('config'))
        method(device.dev, **config)
        return '', 204
    sec = SecurityController.get()
    action = request.form.get('action')
    try:
        get_action(action).run()
        return '', 204
    except StopIteration:
        print("No action found for", action)
    if sec.is_armed() or sec.is_alert():
        if action == 'eventstart':
            print("EVENT START")
            sec.alert()
            get_action('alert').run()
            # SecurityEvent.create(controller=sec, device=key)
            socketio.emit('state change', {'state': sec.state}, namespace='/ws')
            for subscriber in Subscriber.select():
                pass
                try:
                    WebPusher(subscriber.to_dict()).send(
                        json.dumps({'body': "New event alert!!!"}),
                        gcm_key=API_KEY)
                except Exception as e:
                    print("Webpusher:", str(e))
        elif action == 'eventend':
            print("EVENT END")
            try:
                event = SecurityEvent.filter(controller=sec,
                                             device=key).order_by(
                    SecurityEvent.id.desc()).get()
                event.duration = (datetime.datetime.now() - event.datetime).total_seconds()
                print(event.duration)
                event.in_progress = False
                event.save()
                # emit something here
            except SecurityEvent.DoesNotExist:
                abort(412)
    return '', 204


@socketio.on('action', namespace='/ws')
@ws_login_required
def ws_action(data):
    """
    Run actions directly from the Admin panel.
    """
    if not current_user.admin:
        disconnect()
    get_action(data.get('action')).run()


@socketio.on('change state', namespace='/ws')
@ws_login_required
def change_state():
    """
    Toggle the state of the security controller depending on its current state.
    """
    if not current_user.admin:
        disconnect()
    sec = SecurityController.get()
    message = ""
    if sec.state == 'disabled':
        # Set to armed
        sec.arm()
        message = get_action('arm').run()
    elif sec.state == 'armed':
        # Set to disabled
        sec.disable()
        message = get_action('disable').run()
    elif sec.state == 'alert':
        # Restore to armed
        sec.arm()
    emit('state change', {'state': sec.state, 'message': message}, broadcast=True)


@socketio.on('subscribe', namespace='/ws')
@ws_login_required
def subscribe(subscriber):
    """
    Subscribe the browser to push notifications.
    """
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
    """
    Change the bulb's color. Consider moving this to a module in a bulb package.
    """
    emit('push color', {"device": message['device'], "color": message['color']},
         broadcast=True)
    device = get_device(message['device'])
    device.dev.change_color(*utils.RGBfromhex(message['color']),
                            utils.num(message.get('white', 0)), message.get('bright', 100), '41'
                            )


@socketio.on('outmap', namespace="/ws")
@ws_login_required
def reset_color_preview(message):
    """
    Consider moving this to a module in a bulb package.
    """
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


@app.route("/user/password", methods=['POST'])
@fresh_login_required
@login_required
def change_password():
    if current_user.admin:
        user = User.get(username=request.form.get('username'))
    elif current_user.check_password(request.form.get('password')):
        user = current_user
    if request.form.get('new_password') == request.form.get('new_password_confirm'):
        user.set_password(request.form.get('new_password'))
        user.save()
    return redirect(url_for('index'))


@socketio.on('update', namespace='/ws')
@ws_login_required
def ws_update_app():
    if current_user.admin:
        utils.update()


@app.route("/update")
@login_required
def update_app():
    if current_user.admin:
        utils.update()
    return redirect(url_for('index'))


@app.route("/reload")
@login_required
def reload():
    if current_user.admin:
        parser.parse("config.yml")
    return redirect(url_for('index'))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.before_request
def _db_connect():
    """
    This hook ensures that a connection is opened to handle any queries
    generated by the request.
    """
    db.connect()


@app.teardown_request
def _db_close(obj):
    """
    This hook ensures that the connection is closed when we've finished
    processing the request.
    """
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

# TODO: Remove the following
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
