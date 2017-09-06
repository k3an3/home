"""
chromecast.py
~~~~~~~~~~~~~

Module to wrap pychromecast
"""
from functools import wraps

import pychromecast


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
                'text': 'Quit',
                'method': 'quit',
                'class': 'btn-danger'
            }
        )
    }

    def __init__(self, host=None, name=None, port=8009, cec=None):
        self.host = host
        self.name = name
        self.port = port
        self.cec = cec

    def get_cast(f):
        @wraps(f)
        def wrapped(self, *args, **kwargs):
            kwargs['cast'] = get_chromecast(self.host, self.name)
            return f(self, *args, **kwargs)

        return wrapped

    @get_cast
    def test_cast(self, cast):
        self.cast.media_controller.play_media(
            'http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
            'video/mp4')
        self.cast.media_controller.block_until_active(20)

    @get_cast
    def cast_media(self, cast, url, type='video/mp4'):
        cast.media_controller.play_media(url, type)
        cast.media_controller.block_until_active(20)

    @get_cast
    def get_status(self, cast):
        return cast.media_controller.status

    @get_cast
    def stop(self, cast):
        cast.media_controller.stop()

    @get_cast
    def pause(self, cast):
        cast.media_controller.pause()

    @get_cast
    def play(self, cast):
        cast.media_controller.play()

    @get_cast
    def reboot(self, cast):
        cast.reboot()

    @get_cast
    def quit(self, cast):
        cast.quit_app()

    @get_cast
    def volume_up(self, cast, delta=0.1):
        cast.volume_up(delta)

    @get_cast
    def volume_down(self, cast, delta=0.1):
        cast.volume_down(delta)
