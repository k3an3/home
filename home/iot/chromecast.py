"""
chromecast.py
~~~~~~~~~~~~~

Module to wrap pychromecast
"""
from functools import wraps
from time import sleep

import pychromecast

from home import settings


def get_chromecast(host: str = None, name: str = None):
    if host:
        return pychromecast.Chromecast(host=host)
    elif name:
        chromecasts = pychromecast.get_chromecasts()
        return next(cc for cc in chromecasts if cc.device.friendly_name == name)


class Chromecast:
    widget = {
        'buttons': (
            {
                'text': 'TV On',
                'action': 'tv on',
                'class': 'btn-success'
            },
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
                'text': 'Quit',
                'method': 'quit',
                'class': 'btn-danger'
            }
        )
    }
    actions = (
        {
            'name': 'tv on',
            'devices': (
                {
                    'method': 'cast_media',
                    'config': {
                        'url': settings.MEDIA_TEST_URI
                    }
                },
                {
                    'delay': 5,
                    'method': 'quit'
                }
            )
        },
    )

    def __init__(self, host=None, name=None, port=8009, cec=None):
        self.host = host
        self.name = name
        self.port = port
        self.cec = cec
        self.cast = None

    def get_cast(f):
        @wraps(f)
        def wrapped(self, *args, **kwargs):
            self.cast = get_chromecast(self.host, self.name)
            sleep(0.2)
            return f(self, *args, **kwargs)

        return wrapped

    @get_cast
    def test_cast(self):
        self.cast.media_controller.play_media(
            'http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
            'video/mp4')
        self.cast.media_controller.block_until_active(20)

    @get_cast
    def cast_media(self, url, type='video/mp4'):
        self.cast.media_controller.play_media(url, type)
        self.cast.media_controller.block_until_active(20)

    @get_cast
    def get_status(self):
        return self.cast.media_controller.status

    @get_cast
    def stop(self):
        self.cast.media_controller.stop()

    @get_cast
    def pause(self):
        self.cast.media_controller.pause()

    @get_cast
    def play(self):
        self.cast.media_controller.play()

    @get_cast
    def reboot(self):
        self.cast.reboot()

    @get_cast
    def quit(self):
        self.cast.quit_app()

    @get_cast
    def volume_up(self, delta=0.1):
        self.cast.volume_up(delta)

    @get_cast
    def volume_down(self, delta=0.1):
        self.cast.volume_down(delta)
