import datetime
import os

from flask import abort
from flask_login import current_user
from flask_socketio import disconnect, emit

from home import settings
from home.core.models import get_action, devices
from home.web.models import SecurityEvent, SecurityController
from home.web.utils import send_to_subscribers, ws_login_required
from home.web.web import socketio


class Security:
    @staticmethod
    def handle_event(sec, action, app, device):
        """
        Currently, a jumble of things that needs to be majorly refactored
        :param device: 
        :param sec: 
        :param action: 
        :param app: 
        :return: 
        """
        if action == 'eventstart':
            app.logger.info("EVENT START")
            sec.alert()
            get_action('alert').run()
            SecurityEvent.create(controller=sec, device=device.name)
            socketio.emit('state change', {'state': sec.state})
            send_to_subscribers("New event alert")
        elif action == 'eventend':
            app.logger.info("EVENT END")
            try:
                event = SecurityEvent.filter(controller=sec,
                                             device=device.name).order_by(
                    SecurityEvent.id.desc()).get()
                event.duration = (datetime.datetime.now() - event.datetime).total_seconds()
                app.logger.info(event.duration)
                event.in_progress = False
                event.save()
                # emit something here
            except SecurityEvent.DoesNotExist:
                abort(412)


@socketio.on('change state')
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


@socketio.on('get video')
@ws_login_required
def get_video(page=6):
    feeds = [d.name for d in devices if d.driver.name == 'motion']
    recordings = {}
    for dir in settings.SECURITY_FOOTAGE_DIRS:
        recordings[os.path.basename(dir)] = sorted(os.listdir(dir),
                                                   key=lambda x: os.path.getmtime(os.path.join(dir, x)))[-page - 1:-page + 5]
    emit('push video', {'feeds': feeds, 'recordings': recordings})
