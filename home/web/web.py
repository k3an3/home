"""
web.py
~~~~~~

Flask web application for Home.
"""

from flask import Flask, render_template, request, redirect, abort, url_for, session, flash
from flask_login import LoginManager, login_required, current_user
from flask_login import login_user, fresh_login_required, logout_user
from flask_socketio import SocketIO, emit, disconnect
from peewee import DoesNotExist

import home.core.parser as parser
import home.core.utils as utils
from home.core.async import run
from home.core.models import devices, interfaces, get_action, get_device, actions
from home.settings import SECRET_KEY
from home.web.models import *
from home.web.models import User, APIClient
from home.web.utils import ws_login_required, generate_csrf_token, VERSION

try:
    from home.settings import GOOGLE_API_KEY
except ImportError:
    GOOGLE_API_KEY = ""

app = Flask(__name__)
app.secret_key = SECRET_KEY
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.init_app(app)


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
                           clients=APIClient.select(),
                           actions=actions,
                           version=VERSION,
                           )


@app.route('/api/command', methods=['POST'])
def command_api():
    """
    Command API used by devices.
    """
    post = request.form.to_dict()
    try:
        key = APIClient.get(token=post.pop('key'))
    except DoesNotExist:
        abort(403)
    # Send commands directly to device
    if request.form.get('device'):
        device = get_device(post.pop('device'))
        if post.get('method') == 'last':
            method = device.last_method
            kwargs = device.last_kwargs
        else:
            method = utils.method_from_name(device.dev, post.pop('method'))
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
        print("Execute command on", device.name, method, kwargs)
        run(method, **kwargs)
        return '', 204
    sec = SecurityController.get()
    # Trigger an action
    action = request.form.get('action')
    try:
        action = get_action(action)
        print("Run action", action)
        action.run()
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
                        gcm_key=GOOGLE_API_KEY)
                except Exception as e:
                    print("Webpusher:", str(e))
        elif action == 'eventend':
            print("EVENT END")
            try:
                event = SecurityEvent.filter(controller=sec,
                                             device=key.name).order_by(
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
        s.push("Subscribed to push notifications!")


@socketio.on('update', namespace='/ws')
@ws_login_required
def ws_update_app():
    if current_user.admin:
        utils.update()
    emit('update', {}, broadcast=True)


@app.route('/api/update', methods=['POST'])
def api_update_app():
    # Restrict to certain clients
    try:
        APIClient.get(token=request.json.get('secret'))
    except Exception:
        abort(403)
    utils.update()
    emit('update', {}, broadcast=True)


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


# @app.before_request
# def _db_connect():
#    """
#    This hook ensures that a connection is opened to handle any queries
#    generated by the request.
#    """
#    db.connect()
#

@app.teardown_request
def _db_close(obj):
    """
    This hook ensures that the connection is closed when we've finished
    processing the request.
    """
    if not db.is_closed():
        db.close()


app.jinja_env.globals['csrf_token'] = generate_csrf_token


@app.before_request
def csrf_protect():
    if request.method == "POST" and not request.path.startswith('/api/'):
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)


@app.after_request
def add_header(response):
    # response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


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


@app.route("/user/create", methods=['POST'])
@fresh_login_required
@login_required
def create_user():
    if not current_user.admin:
        abort(403)
    if request.form.get('api'):
        APIClient.create(name=request.form.get('username'))
    else:
        if len(request.form.get('password')):
            u = User.create(username=request.form.get('username'),
                            password="")
            u.set_password(request.form.get('password'))
            u.admin = True if request.form.get('admin') else False
            u.save()
        else:
            abort(500)
    return redirect(url_for('index'))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@socketio.on('revoke', namespace='/ws')
@ws_login_required
def revoke(message):
    client = APIClient.get(name=message.get('name'))
    client.delete_instance()


@app.route("/push")
def test_push():
    for subscriber in Subscriber.select():
        subscriber.push("This is only a test!")
    return 204, ''
