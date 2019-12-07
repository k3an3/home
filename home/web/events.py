from flask_login import current_user
from flask_socketio import emit, disconnect
from time import sleep

from home.core import utils as utils, parser as parser
from home.core.models import get_action, get_interface, widgets, MultiDevice
from home.core.tasks import run
from home.settings import LOG_FILE
from home.web.models import APIClient, User, Subscriber, gen_token
from home.web.utils import ws_login_required
from home.web.web import socketio, app, run_session


@socketio.on('admin')
@ws_login_required
def ws_admin(data):
    if not current_user.admin:
        return
    command = data.get('command')
    if command == 'action':
        app.logger.info("({}) Execute action '{}'".format(current_user.username, data.get('action')))
        get_action(data.get('action')).run()
        emit('message', {'class': 'alert-success',
                         'content': "Executing action '{}'.".format(data.get('action'))
                         })
    elif command == 'visible':
        interface = get_interface(data.get('iface'))
        interface.public = not interface.public
        emit('message', {'class': 'alert-success',
                         'content': 'Temporarily changed interface visibility (until server is restarted).'})
    elif command == 'update':
        utils.update()
        emit('update', {}, broadcast=True)
        emit('message', {'class': 'alert-success',
                         'content': 'Updating...'})
    elif command == 'revoke':
        client = APIClient.get(name=data.get('name'))
        client.delete_instance()
        emit('message', {'class': 'alert-success',
                         'content': 'Successfully revoked API permissions.'})
    elif command == 'update permissions':
        client = APIClient.get(name=data.get('name'))
        client.permissions = data.get('perms').replace(' ', '')
        client.save()
        emit('message', {'class': 'alert-success',
                         'content': 'Successfully updated API permissions.'})
    elif command == 'delete':
        user = User.get(username=data.get('name'))
        user.delete_instance()
        emit('message', {'class': 'alert-success',
                         'content': 'Successfully deleted user.'})
    elif command == 'user update permissions':
        user = User.get(username=data.get('name'))
        user._groups = data.get('perms').replace(' ', '')
        user.save()
        emit('message', {'class': 'alert-success',
                         'content': 'Successfully updated User permissions.'})
    elif command == 'user regen token':
        user = User.get(username=data.get('name'))
        user.token = gen_token()
        user.save()
        emit('message', {'class': 'alert-success',
                         'content': 'Successfully invalidated sessions.'})
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
            emit('logs', f.read())
    elif command == 'get config':
        with open('config.yml') as f:
            emit('config', f.read())


@socketio.on('update')
@ws_login_required
def ws_update():
    if current_user.admin:
        utils.update()
        emit('update', {}, broadcast=True)


@socketio.on("widget")
@ws_login_required
def widget(data):
    try:
        target = widgets[data['id']]
    except KeyError:
        # Widget is out of date. Force client reload
        send_message("Interface out of date; reloading", "warning")
        sleep(1)
        emit('reload')
        return
    if current_user.has_permission(target[3]):
        if target[0] == 'method':
            name = target[1].__name__
            app.logger.info(
                "({}) Execute {} on {} with config {}".format(current_user.username, name, target[3].name,
                                                              target[2]))
            func = target[1]
            args = target[2]
            try:
                if target[3].driver.noserialize or type(target[3]) is MultiDevice:
                    func(**args)
                else:
                    run(func, **args)
            except Exception as e:
                app.logger.error("Error running {}: {}".format(name, str(e)))
                send_message("Error running \"{}\"!".format(name), 'danger')
            else:
                send_message("Successfully ran \"{}\".".format(name), 'success')
        elif target[0] == 'action':
            app.logger.info("({}) Execute action {}".format(current_user.username, target[1]))
            send_message("Executing action \"{}\"".format(target[1]))
            target[1].run()
    else:
        disconnect()


@socketio.on("device state")
@ws_login_required(check_device=True)
def device_state(data, device):
    try:
        emit('device state', {'device': device.name, 'state': device.dev.get_state()})
    except AttributeError:
        emit('device state', {'device': device.name, 'state': None})


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


@socketio.on('connect')
def connect():
    emit('run session', run_session)


def send_message(msg: str, style: str = 'info'):
    emit('message',
         {'class': 'alert-' + style,
          'content': msg
          })
