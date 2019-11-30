"""
web.py
~~~~~~

Flask web application for Home.
"""
import flask_assets
from flask import Flask, render_template, request, redirect, abort, url_for, session, flash
from flask_login import LoginManager, login_required, current_user
from flask_login import login_user, logout_user
from flask_socketio import SocketIO, emit
from peewee import DoesNotExist
from webassets.loaders import PythonLoader as PythonAssetsLoader

import home.core.parser as parser
import home.core.utils as utils
from home.core.models import devices, interfaces, get_action, actions, get_driver, get_display, displays
from home.settings import SECRET_KEY, SENTRY_URL, CUSTOM_AUTH_HANDLERS
from home.web.models import *
from home.web.models import User, APIClient
from home.web.utils import generate_csrf_token, VERSION, api_auth_required, send_to_subscribers, \
    handle_task, get_qr, get_widgets, get_action_widgets, ldap_auth, filter_by_permission

try:
    from home.settings import GOOGLE_API_KEY
except ImportError:
    GOOGLE_API_KEY = ""

app = Flask(__name__)
app.secret_key = SECRET_KEY
if not DEBUG:
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )
socketio = SocketIO(app, cors_allowed_origins=[])
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
    print(devices.values())
    sec = SecurityController.get()
    events = sec.events
    interface_list = []
    for i in interfaces:
        interface_list.append((i, [d for d in devices.values() if d.driver and d.driver.interface == i and
                                   (i.public or current_user.is_authenticated and current_user.has_permission(d))]))
    if current_user.is_active:
        widget_html = get_widgets(current_user) + get_action_widgets(current_user)
        return render_template('index.html',
                               interfaces=interface_list,
                               devices=filter_by_permission(current_user, devices.values()),
                               sec=sec,
                               events=events,
                               clients=APIClient.select(),
                               actions=filter_by_permission(current_user, actions),
                               version=VERSION,
                               debug=DEBUG,
                               qr=get_qr(),
                               widgets=widget_html,
                               displays=displays,
                               users=User.select()
                               )
    return render_template('index.html', interfaces=interface_list, devices=devices.values())


@app.route('/api/command', methods=['POST'])
@api_auth_required
def command_api(client):
    """
    Command API used by devices.
    """
    post = request.form.to_dict()
    post.pop('key', None)
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
            app.logger.warning("({}) Insufficient API permissions to execute action '{}'".format(client.name, action))
            abort(403)
        return '', 204
    except StopIteration:
        app.logger.warning("({}) Action '{}' not found".format(client.name, request.form.get('action')))
    return '', 204


@app.route('/api/update', methods=['POST'])
@api_auth_required(has_permission='update')
def api_update_app(client, *args, **kwargs):
    socketio.emit('update', {}, broadcast=True)
    utils.update()


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
def user_loader(token):
    try:
        return User.get(token=token)
    except DoesNotExist:
        return None


@login_manager.request_loader
def load_user_from_request(request):
    for handler in CUSTOM_AUTH_HANDLERS:
        user = handler(request)
        if user:
            return user


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


@app.route("/api/notify", methods=['POST'])
@api_auth_required(has_permission='notify')
def push_notify(client, data):
    # Expects JSON payload, hence the data argument
    send_to_subscribers(data['msg'], groups=data.get('groups', []))
    return '', 204


@app.route("/displays/<disp>")
@login_required
def display(disp):
    disp = get_display(disp)
    if current_user.has_permission(disp):
        dashboard = disp.render()
        widget_html = get_widgets(current_user) + get_action_widgets(current_user)
        return render_template(disp.template or 'display.html',
                               dashboard=dashboard,
                               widgets=widget_html
                               )


@app.route("/display/<path:path>")
def guest_auth(path):
    if path == get_qr()[1].split('/')[-1]:
        if not current_user.is_authenticated:
            login_user(User.get(username='guest'))
        return redirect(url_for('display'))
    abort(403)


@app.template_filter('slugify')
def slugify(text: str):
    return text.replace(' ', '-')


def send_message(msg: str, style: str = 'info'):
    emit('message',
         {'class': 'alert-' + style,
          'content': msg
          })
