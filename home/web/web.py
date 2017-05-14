"""
web.py
~~~~~~

Flask web application for Home.
"""

from flask import Flask, render_template, request, redirect, abort, url_for, session, flash
from flask_login import LoginManager, login_required, current_user
from flask_login import login_user, fresh_login_required, logout_user
from flask_socketio import SocketIO, emit, disconnect

import home.core.parser as parser
import home.core.utils as utils
from home.core.models import devices, interfaces, get_action, actions, get_interface, get_driver
from home.settings import SECRET_KEY, DEBUG, LOG_FILE
from home.web.models import *
from home.web.models import User, APIClient
from home.web.utils import ws_login_required, generate_csrf_token, VERSION, api_auth_required, send_to_subscribers, \
    handle_task

try:
    from home.settings import GOOGLE_API_KEY
except ImportError:
    GOOGLE_API_KEY = ""

app = Flask(__name__)
app.secret_key = SECRET_KEY
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.init_app(app)
app.jinja_env.globals['csrf_token'] = generate_csrf_token


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
    if current_user:
        with open(LOG_FILE) as f:
            logs = f.read()
        return render_template('index.html',
                               interfaces=interface_list,
                               devices=devices,
                               sec=sec,
                               events=events,
                               clients=APIClient.select(),
                               actions=actions,
                               version=VERSION,
                               logs=logs,
                               debug=DEBUG,
                               )


@app.route('/api/command', methods=['POST'])
@api_auth_required
def command_api(client):
    """
    Command API used by devices.
    """
    post = request.form.to_dict()
    # Send commands directly to device
    if request.form.get('device'):
        handle_task(post, client)
        return '', 204
    sec = SecurityController.get()
    # Trigger an action
    action = request.form.get('action')
    if sec.is_armed() or sec.is_alert() and 'event' in action:
        # TODO: This thing is really a mess
        sec_ = get_driver('security').klass
        sec_.handle_event(sec, action, app, client)
        return '', 204
    try:
        action = get_action(action)
        app.logger.info("({}) Execute action {}".format(client.name, action))
        action.run()
        return '', 204
    except StopIteration:
        app.logger.warning("({}) Action '{}' not found".format(client.name, request.form.get('action')))
    return '', 204


@socketio.on('admin')
@ws_login_required
def ws_admin(data):
    if not current_user.admin:
        disconnect()
    command = data.get('command')
    if command == 'action':
        app.logger.info("({}) Execute action {}".format(current_user.username, data.get('action')))
        get_action(data.get('action')).run()
    elif command == 'visible':
        interface = get_interface(data.get('iface'))
        interface.public = not interface.public
    elif command == 'update':
        utils.update()
        emit('update', {}, broadcast=True)
    elif command == 'revoke':
        client = APIClient.get(name=data.get('name'))
        client.delete_instance()


@socketio.on('subscribe')
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


@app.route('/api/update', methods=['POST'])
@api_auth_required
def api_update_app(client):
    socketio.emit('update', {}, broadcast=True)
    utils.update()


@socketio.on('update')
@ws_login_required
def ws_update():
    if current_user.admin:
        utils.update()
        emit('update', {}, broadcast=True)


@app.route("/update")
@login_required
def update_app():
    if current_user.admin:
        utils.update()
        socketio.emit('update', {}, broadcast=True)
    return redirect(url_for('index'))


@app.route("/reload")
@login_required
def reload():
    if current_user.admin:
        try:
            parser.parse("config.yml")
        except Exception:
            flash('Error in device config file. Please fix and reload.')
        else:
            flash('Device config reload successful.')
    return redirect(url_for('index'))


@app.before_request
def csrf_protect():
    if request.method == "POST" and not request.path.startswith('/api/'):
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)


@app.before_request
def session_permanent():
    session.permanent = True


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


@app.route("/push", methods=['GET', 'POST'])
@api_auth_required
def test_push(**kwargs):
    send_to_subscribers("This is only a test.")
    return '', 204
