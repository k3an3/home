"""
plug.py
~~~~~~~

Module for communicating with smart plugs
"""
from abc import abstractmethod

import broadlink
from pyvesync import VeSync

from home.iot.power import Power

PORT = 80


class Plug(Power):
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

    @abstractmethod
    def get_state(self) -> str:
        pass


class BroadlinkPlug(Plug):
    """
    A class representing a single Broadlink smart plug
    """

    def __init__(self, host: str, mac: str):
        self.host = host
        self.mac = mac

    def _get_plug(self):
        device = broadlink.gendevice(0x2711, (self.host, 80), bytearray.fromhex(self.mac.replace(':', '')))
        device.auth()
        return device

    def power(self, state: bool):
        device = self._get_plug()
        device.set_power(state)

    def get_state(self):
        device = self._get_plug()
        return 'on' if device.check_power() else 'off'


class EtekcityPlug(Plug):
    def __init__(self, email: str, password: str, index: int = 0, time_zone: str = 'America/New_York'):
        self.email = email
        self.password = password
        self.time_zone = time_zone
        self.index = index

    def _get_plug(self):
        manager = VeSync(self.email, self.password, self.time_zone)
        manager.login()
        manager.update()
        return manager.outlets[self.index]

    def power(self, state: str) -> None:
        device = self._get_plug()
        if state:
            device.turn_on()
        else:
            device.turn_off()

    def get_state(self) -> str:
        device = self._get_plug()
        return 'on' if device.is_on else 'off'
