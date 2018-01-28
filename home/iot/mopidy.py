"""
mopidy.py
~~~~~~~~~

Websocket JSONRPC client for the Mopidy media server
"""
import json

import requests
from flask_socketio import disconnect, emit
from requests.auth import HTTPBasicAuth

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

SPOTIFY_API = 'https://api.spotify.com/v1/{}'


class Spotify:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

    def spotify_get(self, query):
        if not self.token:
            self.auth(self.client_id, self.client_secret)
        return requests.get(SPOTIFY_API.format(query), headers={'Authorization': 'Bearer ' + self.token}).json()

    def auth(self, cid, cs):
        data = {
            'grant_type': 'client_credentials'
        }
        r = requests.post('https://accounts.spotify.com/api/token',
                         data=data,
                         auth=HTTPBasicAuth(cid, cs))
        return r.json().get('access_token')

    def get_album_art(self, album_id, image=1):
        r = self.spotify_get('albums/' + album_id)['images'][image]['url']
        return r


class Mopidy:
    widget = {
        'buttons': (
            {
                'text': 'Play',
                'method': 'play',
                'class': 'btn-success'
            },
            {
                'text': 'Pause',
                'method': 'pause',
                'class': 'btn-warning'
            },
            {
                'text': 'Stop',
                'method': 'clear',
                'class': 'btn-danger'
            },
            {
                'text': 'Next',
                'method': 'next',
            },
            {
                'text': 'Prev',
                'method': 'previous'
            },
        )
    }

    def __init__(self, host, client_id=None, client_secret=None):
        self.host = "http://" + host + ":6680/mopidy/rpc"
        self.id = 1
        self.spotify = Spotify(client_id, client_secret)
        self.song = None

    def send(self, method, **kwargs):
        msg = {"jsonrpc": "2.0", "id": self.id, 'method': method, 'params': dict(kwargs)}
        return requests.post(self.host, data=json.dumps(msg)).json()

    def get_current_track(self):
        song = self.send('core.playback.get_current_tl_track')['result']['track']
        if not self.song or not song['uri'] == self.song['uri']:
            self.song = song
            self.song['art'] = self.spotify.get_album_art(song['album']['uri'].split(':')[2])
        return self.song

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

    def custom(self, target, key, value):
        if value == 'true':
            value = True
        elif value == 'false':
            value = False
        return self.send(target, **{key: value})

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
            'art': track['art']
        }))
