"""
web.py
~~~~~~

Flask web application for Home.
"""
import flask_assets
from flask import Flask, render_template, request, redirect, abort, url_for, session, flash
from flask_login import LoginManager, login_required, current_user
from flask_login import login_user, logout_user
from flask_socketio import SocketIO, emit, disconnect
from peewee import DoesNotExist
from webassets.loaders import PythonLoader as PythonAssetsLoader

import home.core.parser as parser
import home.core.utils as utils
from home.core.models import devices, interfaces, get_action, actions, get_interface, get_driver, widgets, get_device
from home.settings import SECRET_KEY, LOG_FILE, PUBLIC_GROUPS
from home.web.models import *
from home.web.models import User, APIClient
from home.web.utils import ws_login_required, generate_csrf_token, VERSION, api_auth_required, send_to_subscribers, \
    handle_task, get_qr, get_widgets, get_action_widgets, ldap_auth

try:
    from home.settings import GOOGLE_API_KEY
except ImportError:
    GOOGLE_API_KEY = ""

app = Flask(__name__, template_folder='templates')
app.secret_key = SECRET_KEY
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.init_app(app)
app.jinja_env.globals['csrf_token'] = generate_csrf_token
assets = flask_assets.Environment()
assets.init_app(app)
assets_loader = PythonAssetsLoader('home.web.assets')
# Experimental oauth support
# oauth = OAuth2Provider(app)
for name, bundle in assets_loader.load_bundles().items():
    assets.register(name, bundle)

try:
    from home.settings import LDAP_CONFIG

    app.config.update(LDAP_CONFIG)
except ImportError:
    ldap = None


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
    if current_user.is_active:
        widget_html = get_widgets(current_user) + get_action_widgets(current_user)
        if current_user.admin:
            with open('config.yml') as f:
                config = f.read()
        return render_template('index.html',
                               interfaces=interface_list,
                               devices=devices,
                               sec=sec,
                               events=events,
                               clients=APIClient.select(),
                               actions=actions,
                               version=VERSION,
                               debug=DEBUG,
                               qr=get_qr(),
                               widgets=widget_html,
                               config=config
                               )
    return render_template('index.html', interfaces=interface_list, devices=devices)


@app.route('/api/command', methods=['POST'])
@api_auth_required
def command_api(client):
    """
    Command API used by devices.
    """
    post = request.form.to_dict()
    post.pop('key')
    # Send commands directly to device
    if request.form.get('device'):
        if handle_task(post, client):
            return '', 204
        abort(403)
    sec = SecurityController.get()
    # Trigger an action
    action = request.form.get('action').strip()
    if 'event' in action and sec.is_armed() or sec.is_alert():
        if client.has_permission('sec'):
                app.logger.info('({}) Triggered security event'.format(client.name))
                # TODO: This thing is really a mess
                sec_ = get_driver('security').klass
                sec_.handle_event(sec, action, app, client)
                return '', 204
        else:
            app.logger.warning('({}) Insufficient API permissions to trigger security event'.format(client.name))
            abort(403)
    try:
        action = get_action(action)
        if client.has_permission(action.group):
            app.logger.info("({}) Execute action {}".format(client.name, action))
            action.run()
        else:
            app.logger.warning("({}) Insufficient API permissions to execute action {}".format(client.name, action))
            abort(403)
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
    elif command == 'refresh_display':
        emit('display refresh', broadcast=True)
    elif command == 'update config':
        try:
            parser.parse(data=data['config'])
        except Exception as e:
            parser.parse(file='config.yml')
            emit('message', {'class': 'alert-danger',
                             'content': 'Error parsing device configuration. ' + str(e)})
        else:
            with open('config.yml', 'w') as f:
                f.write(data['config'])
            emit('message', {'class': 'alert-success',
                             'content': 'Successfully updated device configuration.'})
    elif command == 'refresh logs':
        with open(LOG_FILE) as f:
            logs = f.read()
        emit('logs', logs)


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
    if not client.has_permission('update'):
        abort(403)
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
        except Exception as e:
            app.logger.error(e)
            flash('Error in device config file. Please fix and reload.')
        else:
            flash('Device config reload successful.')
            socketio.emit('reload', {}, broadcast=True)
    return redirect(url_for('index'))


@app.route("/restart")
@login_required
def restart():
    if current_user.admin:
        socketio.emit('update', {}, broadcast=True)
        utils.reload()
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
    username = request.form.get('username')
    password = request.form.get('password')
    created = False
    try:
        user = User.get(username=username)
    except DoesNotExist:
        if USE_LDAP:
            user = ldap_auth(username, password)
            created = True
    if user and not user.username == 'guest':
        if created or user.check_password(password):
            login_user(user)
            flash('Logged in successfully.')
    if not user:
        flash('Invalid credentials.')
    return redirect(url_for('index'))


@app.route("/user/password", methods=['POST'])
@login_required
def change_password():
    if current_user.admin:
        user = User.get(username=request.form.get('username'))
    elif current_user.check_password(request.form.get('password')):
        user = current_user
    if not user.ldap and request.form.get('new_password') == request.form.get('new_password_confirm'):
        user.set_password(request.form.get('new_password'))
        user.save()
    if user.ldap:
        flash('Sorry, cannot change passwords for LDAP accounts.')
    return redirect(url_for('index'))


@app.route("/user/create", methods=['POST'])
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
def test_push(client):
    if not client.has_permission('test'):
        abort(403)
    send_to_subscribers("This is only a test.")
    return '', 204


@app.route("/display")
@login_required
def display():
    widget_html = get_widgets(current_user) + get_action_widgets(current_user)
    return render_template('display.html',
                           widgets=widget_html
                           )


@app.route("/display/<path:path>")
def guest_auth(path):
    if path == get_qr()[1].split('/')[-1]:
        if not current_user.is_authenticated:
            login_user(User.get(username='guest'))
        return redirect(url_for('display'))
    abort(403)


@socketio.on("widget")
@ws_login_required
def widget(data):
    target = widgets[data['id']]
    if target[3].group in current_user.groups or target[3].group in PUBLIC_GROUPS or current_user.admin:
        if target[0] == 'method':
            app.logger.info(
                "({}) Execute {} on {} with config {}".format(current_user.username, target[1].__name__, target[3].name,
                                                              target[2]))
            func = target[1]
            args = target[2]
            func(**args)
        elif target[0] == 'action':
            app.logger.info("({}) Execute action {}".format(current_user.username, target[1]))
            target[1].run()
    else:
        disconnect()


@socketio.on("device state")
@ws_login_required
def device_state(data):
    target = get_device(data['device'])
    if target.group in current_user.groups or target.group in PUBLIC_GROUPS or current_user.admin:
        try:
            emit('device state', {'device': target.name, 'state': target.dev.get_state()})
        except AttributeError:
            emit('device state', {'device': target.name, 'state': None})


@app.template_filter('slugify')
def slugify(text: str):
    return text.replace(' ', '-')
