"""
mopidy.py
~~~~~~~~~

Websocket JSONRPC client for the Mopidy media server
"""
import json
from threading import Thread
from time import sleep

import requests
import websocket
from flask_socketio import disconnect, emit

from home.core.models import get_device
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

SPOTIFY_API = 'https://api.spotify.com/v1/{}/{}'


def get_album_art(album_id, image=1):
    return requests.get(SPOTIFY_API.format('albums', album_id)).json().get('images')[image]


class Mopidy:
    def __init__(self, host):
        self.host = host
        self.ws = websocket.WebSocketApp("ws://{}:6680/mopidy/ws".format(host),
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.t = Thread(target=self.ws.run_forever)
        self.t.start()
        self.id = 1
        self.track = None

    def send(self, method, **kwargs):
        msg = {"jsonrpc": "2.0", "id": 1, 'method': method, 'params': dict(kwargs)}
        self.id += 1
        self.ws.send(json.dumps(msg))

    def on_open(self, ws):
        pass

    def on_message(self, ws, message):
        j = json.loads(message)
        event = j.get('event')
        state = j.get('new_state')
        track = j.get('tl_track')
        result = j.get('result')
        if result:
            if result.get('track'):
                self.track = result.get('track')
        if event == 'tracklist_changed':
            socketio.emit('tracklist changed', broadcast=True, namespace='/mopidy')
        if state == 'playing':
            socketio.emit('playback state', json.dumps({'state': 'playing'}), broadcast=True, namespace='/mopidy')
        elif state == 'paused':
            socketio.emit('playback state', json.dumps({'state': 'paused'}), broadcast=True, namespace='/mopidy')
        if track:
            track = track.get('track')
            self.track = track
            socketio.emit('track', json.dumps({
                'title': track['name'],
                'artists': ', '.join(artist['name'] for artist in track['artists']),
                'album': track['album']['name'],
                'art': get_album_art(track['album']['uri'].split(':')[2])
            }), broadcast=True, namespace='/mopidy')

        print(j)

    def on_error(self, ws, error):
        print("Mopidy websocket error!", error)

    def on_close(self, ws):
        print("Mopidy websocket closed")

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

    def get_images(self, uris, index=0):
        return self.send('core.library.get_images', uris=uris)['result'].popitem()[1][index]


@socketio.on('mopidy', namespace='/mopidy')
@ws_optional_auth
def mopidy_ws(data, **kwargs):
    mopidy = get_device(data.pop('device')).dev
    auth = kwargs.pop('auth', False)
    action = data.pop('action')
    if not auth and action not in UNAUTH_COMMANDS:
        print("Disconnected client from Mopidy endpoint, not authorized/invalid command")
        disconnect()
    if action == 'search':
        results = mopidy.search(**data)
        try:
            results = results['result'][0]['tracks']
            emit('search results', json.dumps(results))
        except Exception as e:
            pass
    elif action == 'add_track':
        mopidy.add_track(**data)
        print("Queued track!")
    elif action == 'get_current_track':
        while not mopidy.track:
            mopidy.get_current_track()
            sleep(1)
        emit('track', json.dumps({
            'title': mopidy.track['name'],
            'artists': ', '.join(artist['name'] for artist in mopidy.track['artists']),
            'album': mopidy.track['album']['name'],
            'art': get_album_art(mopidy.track['album']['uri'].split(':')[2])
        }))
