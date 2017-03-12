"""
mopidy.py
~~~~~~~~~

Websocket JSONRPC client for the Mopidy media server
"""
import json

import websocket
from flask_socketio import disconnect, emit

from home.core.models import get_device
from home.core.utils import method_from_name
from home.web.utils import ws_optional_auth
from home.web.web import socketio

UNAUTH_COMMANDS = (
    'search',
    'get_tracks',
    'add_track',
    'get_state',
    'get_current_track',
    'get_time_position',
)


class Mopidy:
    def __init__(self, host):
        self.host = host
        self.ws = websocket.WebSocket()
        self.ws.connect("ws://{}:6680/mopidy/ws".format(host),
                        on_message=self.on_message,
                        on_error=self.on_error,
                        on_close=self.on_close)
        self.id = 1

    def send(self, method, **kwargs):
        msg = {"jsonrpc": "2.0", "id": 1, 'method': method, 'params': dict(kwargs)}
        self.id += 1
        self.ws.send(json.dumps(msg))
        return self.ws.recv()

    def on_message(self, ws, message):
        j = json.loads(message)
        print(j)

    def on_error(self, ws, error):
        pass

    def on_close(self, ws):
        pass

    def get_current_track(self):
        return self.send('core.playback.get_current_tl_track')

    def get_state(self):
        return self.send('core.playback.get_state')

    def get_time_position(self):
        return self.send('core.playback.get_time_position')

    def get_volume(self):
        return self.send('core.playback.get_volume')

    def next(self):
        return self.send('core.playback.next')

    def pause(self):
        return self.send('core.playback.pause')

    def play(self):
        return self.send('core.playback.play')

    def previous(self):
        return self.send('core.playback.previous')

    def resume(self):
        return self.send('core.playback.resume')

    def stop(self):
        return self.send('core.playback.stop')

    def get_playlists(self):
        return self.send('core.playlists.as_list')

    def add_track(self, uri):
        return self.send('core.tracklist.add', uri=uri)

    def get_tracks(self):
        return self.send('core.tracklist.get_tracks')

    def search(self, query):
        return self.send('core.library.search', any=[query])


@socketio.on('mopidy', namespace='/mopidy')
@ws_optional_auth
def mopidy_ws(data, **kwargs):
    import datetime
    start = datetime.datetime.now()
    mopidy = get_device(data.pop('device')).dev
    auth = kwargs.pop('auth')
    method = method_from_name(Mopidy, data.pop('action'))
    if not auth and method not in UNAUTH_COMMANDS:
        disconnect()
    print(datetime.datetime.now() - start)
    emit('search results', method(mopidy, **data))
