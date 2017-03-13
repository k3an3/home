from subprocess import Popen


class Audio:
    @staticmethod
    def test():
        Popen(['/usr/bin/aplay', '/usr/share/sounds/alsa/Rear_Center.wav'])

    def play(self, filename):
        # Terrible, terrible code
        if filename.endswith('.mp3'):
            bin = '/usr/bin/mpg321'
        else:
            bin = '/usr/bin/aplay'
        Popen([bin, filename])
