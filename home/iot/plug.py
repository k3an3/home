import socket

import broadlink

PORT = 80


class Plug:
    """
    A class representing a single Broadlink smart plug
    """
    def __init__(self, host, mac):
        self.device = broadlink.device(host=(host, PORT,), mac=bytearray.fromhex(''.join(mac.split(':'))))
        try:
            self.auth()
        except socket.timeout:
            print("Plug: Failed to auth with plug at", host)

    def auth(self):
        return self.device.auth()

    def power(self, state):
        self.device.set_power(state)

    def on(self):
        self.power(True)

    def off(self):
        self.power(False)

    def get_state(self):
        return self.device.check_power()
