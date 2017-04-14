"""
mopidy.py
~~~~~~~~~

Websocket JSONRPC client for the Mopidy media server
"""
import json

import requests
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
        self.host = "http://" + host + ":6680/mopidy/rpc"
        self.id = 1

    def send(self, method, **kwargs):
        msg = {"jsonrpc": "2.0", "id": self.id, 'method': method, 'params': dict(kwargs)}
        return requests.post(self.host, data=json.dumps(msg)).json()

    def get_current_track(self):
        return self.send('core.playback.get_current_tl_track')['result']['track']

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

    def play(self, track=None):
        return self.send('core.playback.play', tl_track=track)

    def previous(self):
        return self.send('core.playback.previous')

    def clear(self):
        return self.send('core.tracklist.clear')

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
        r = mopidy.add_track(**data)
    elif action == 'get_current_track':
        track = mopidy.get_current_track()
        emit('track', json.dumps({
            'title': track['name'],
            'artists': ', '.join(artist['name'] for artist in track['artists']),
            'album': track['album']['name'],
            'art': get_album_art(track['album']['uri'].split(':')[2])
        }))
