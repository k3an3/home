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

    def cast_media(self, url, type='video/mp4'):
        self.cast.media_controller.play_media(url, type)
        self.cast.media_controller.block_until_active(20)

    def get_status(self):
        return self.cast.media_controller.status

    def stop(self):
        self.cast.media_controller.stop()

    def pause(self):
        self.cast.media_controller.pause()

    def play(self):
        self.cast.media_controller.play()

    def reboot(self):
        self.cast.reboot()

    def quit(self):
        self.cast.quit_app()

    def volume_up(self, delta=0.1):
        self.cast.volume_up(delta)

    def volume_down(self, delta=0.1):
        self.cast.volume_down(delta)
