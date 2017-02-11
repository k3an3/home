"""
wol.py
~~~~~~

Wrapper for wake-on-lan automation
"""
from wakeonlan import wol


class WakeOnLAN:
    def __init__(self, mac, host=None, port=None):
        self.mac = mac
        self.host = host
        self.port = port

    def wake(self):
        wol.send_magic_packet(self.mac, ip_address=self.host, port=self.port)
