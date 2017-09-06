"""
plug.py
~~~~~~~

Module for communicating with the Broadlink smart plug
"""

import broadlink

PORT = 80


class Plug:
    widget = {
        'buttons': (
            {
                'text': 'On',
                'method': 'on'
            },
            {
                'text': 'Off',
                'method': 'off',
                'class': 'btn-danger'
            },
        )
    }
    """
    A class representing a single Broadlink smart plug
    """

    def __init__(self, host, mac):
        self.host = host
        self.mac = mac

    def get_plug(self):
        device = broadlink.gendevice(0x2711, (self.host, 80), bytearray.fromhex(self.mac.replace(':', '')))
        device.auth()
        return device

    def power(self, state):
        device = self.get_plug()
        device.set_power(state)

    def on(self):
        self.power(True)

    def off(self):
        self.power(False)

    def get_state(self):
        device = self.get_plug()
        return device.check_power()
