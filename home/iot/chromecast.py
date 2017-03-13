"""
chromecast.py
~~~~~~~~~~~~~

Module to wrap pychromecast
"""
import pychromecast


class Chromecast:
    def __init__(self, host=None, name=None, port=8009, cec=None):
        self.host = host
        self.name = name
        self.port = port
        self.cec = cec
        if host:
            self.cast = pychromecast.Chromecast(host=host)
        elif name:
            chromecasts = pychromecast.get_chromecasts()
            self.cast = next(cc for cc in chromecasts if cc.device.friendly_name == name)

    def test_cast(self):
        self.cast.media_controller.play_media(
            'http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
            'video/mp4')
        self.cast.media_controller.block_until_active(20)

    def get_status(self):
        return self.cast.media_controller.status
