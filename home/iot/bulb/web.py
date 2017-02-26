from flask_socketio import emit

from home.core import utils as utils
from home.core.models import get_device
from home.web.utils import ws_login_required
from home.web.web import socketio


@socketio.on('change color', namespace='/ws')
@ws_login_required
def request_change_color(message):
    """
    Change the bulb's color.
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
    Reset the color preview
    """
    emit('preview reset', message['color'], broadcast=True)
