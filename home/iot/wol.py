"""
wol.py
~~~~~~

Wrapper for wake-on-lan automation
"""
import subprocess

from wakeonlan import wol


class WakeOnLAN:
    def __init__(self, mac, host=None, port=None, manual_interface=None):
        self.mac = mac
        self.host = host
        self.port = port
        self.interface = manual_interface

    def wake(self):
        if self.interface:
            subprocess.run(['sudo', '/usr/sbin/ether-wake', '-i', self.interface, self.mac])
        else:
            wol.send_magic_packet(self.mac, ip_address=self.host, port=self.port)
