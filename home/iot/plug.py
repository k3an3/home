"""
plug.py
~~~~~~~

Module for communicating with the Broadlink smart plug
"""
import socket

import broadlink

PORT = 80


class Plug:
    """
    A class representing a single Broadlink smart plug
    """
    def __init__(self, host, mac):
        self.device = broadlink.gendevice(0x2711, (host, 80), bytearray.fromhex(mac.replace(':', '')))
        try:
            self.auth()
        except socket.timeout:
            print("Plug: Failed to auth with plug at", host)

    def auth(self):
        return self.device.auth()

    def power(self, state):
        try:
            self.device.set_power(state)
        except Exception as e:
            print("Plug: " + str(e))

    def on(self):
        self.power(True)

    def off(self):
        self.power(False)

    def get_state(self):
        return self.device.check_power()
