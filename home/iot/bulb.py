#!/usr/bin/env python3
"""
bulb.py
~~~~~~~

This module is for communicating with the MagicHome LED bulb over the network.

Wire protocol:

-------------------------------------
|header(1)|data(5-70)|0f|checksum(1)|
-------------------------------------

header:
    31 color & white
    41 camera
    51 custom
    61 function

color, white, camera (8 bytes):
    00-ff red
    00-ff green
    00-ff blue
    00-ff white
    mode:
        0f white
        f0 color

functions (5 bytes):
    25-38 modes
    1f-01 speed (decreasing)
    0f who knows

custom (70 bytes):
    64 bytes of r, g, b, 0 (empty color is 0x01020300)
    1f-01 speed (decreasing)
    3a,3b,3c gradual, jumping, strobe
    ff tail

tail:
    0f
    checksum (sum of data fields)
"""
import socket
import sys

from astral import Astral
from datetime import datetime
from flask_socketio import emit
from typing import Dict

from home import settings
from home.core import utils as utils
from home.core.models import get_device
from home.core.utils import num
from home.web.utils import ws_login_required
from home.web.web import socketio

SUPPORTED_MODES = ['31', '41', '61']
SUPPORTED_FUNCTIONS = list(range(25, 39))
TAIL = '0f'

seven_color_cross_fade = 0x25
red_gradual_change = 0x26
green_gradual_change = 0x27
blue_gradual_change = 0x28
yellow_gradual_change = 0x29
cyan_gradual_change = 0x2a
purple_gradual_change = 0x2b
white_gradual_change = 0x2c
red_green_cross_fade = 0x2d
red_blue_cross_fade = 0x2e
green_blue_cross_fade = 0x2f
seven_color_strobe_flash = 0x30
red_strobe_flash = 0x31
green_strobe_flash = 0x32
blue_stobe_flash = 0x33
yellow_strobe_flash = 0x34
cyan_strobe_flash = 0x35
purple_strobe_flash = 0x36
white_strobe_flash = 0x37
seven_color_jumping = 0x38

CONTROL_PORT = 5577
# The HFLPB100's control/debug module
HF_COMMAND_PORT = 48899
HF_COMMAND = 'HF-A11ASSISTHREAD'.encode()
HF_COMMAND_OK = '+ok'.encode()

prepare_hex = lambda x: format(x, 'x').zfill(2)
socket.setdefaulttimeout(20)


def calc_sunlight() -> int:
    """
    Calculate an appropriate brightness for the bulb depending on
    current sunlight.
    :return: White brightness
    """
    a = Astral()
    a.solar_depression = 'civil'
    city = a[settings.LOCATION]
    sun = city.sun(date=datetime.now(), local=True)
    dt = datetime.now(sun['sunrise'].tzinfo)
    if dt.hour < 4 or dt.hour >= 22:
        return {'red': 255}
    elif dt < sun['sunrise']:
        return {'white': 255 - (sun['sunrise'] - dt).total_seconds() / 3600 * 200 / 6}
    elif dt > sun['sunset']:
        return {'white': 255 - (dt - sun['sunset']).total_seconds() / 3600 * 200 / 6}
    else:
        return {'white': 255}


class Bulb:
    """
    A class representing a single MagicHome LED Bulb.
    """
    widget = {
        'buttons': (
            {
                'text': 'Auto',
                'function': 'sunlight',
                'class': 'btn-info'
            },
            {
                'text': 'On',
                'function': 'on',
            },
            {
                'text': 'Off',
                'function': 'off',
                'class': 'btn-danger'
            }
        ),
        'form': {
            'buttons': (
                {}
            )
        }
    }

    def __init__(self, host):
        self.host = host

    def auth(self) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(HF_COMMAND, (self.host, HF_COMMAND_PORT))
        s.sendto(HF_COMMAND_OK, (self.host, HF_COMMAND_PORT))

    def change_color(self, red: int = 0, green: int = 0, blue: int = 0, white: int = 0, brightness: int = 255,
                     mode: str = '31', function: str = None, speed: str = '1f') -> None:
        """
        Provided RGB values and a brightness, change the color of the
        bulb with a TCP socket.
        """
        if mode not in SUPPORTED_MODES:
            raise NotImplementedError

        if function:
            if num(function) not in SUPPORTED_FUNCTIONS:
                raise NotImplementedError
            data = bytearray.fromhex(mode + function + speed + TAIL)
        else:
            red, green, blue, white, brightness = num(red, green, blue, white, brightness)
            red = num(red * brightness / 255)
            green = num(green * brightness / 255)
            blue = num(blue * brightness / 255)
            white = num(white * brightness / 255)
            color_hex = (prepare_hex(red) + prepare_hex(green) + prepare_hex(blue)
                         + prepare_hex(white))
            if white:
                color_mode = '0f'
            else:
                color_mode = 'f0'
            # Build packet
            data = bytearray.fromhex(mode + color_hex
                                     + color_mode + TAIL)
        try:
            # Compute checksum
            data.append(sum(data) % 256)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, CONTROL_PORT))
            sock.send(data)
            sock.close()
        except Exception as e:
            print(e)

    def sunlight(self) -> None:
        self.change_color(**calc_sunlight())

    def fade(self, start: Dict = None, stop: Dict = None, bright: int = None, speed: int = 1) -> None:
        speed = abs(speed)
        if start:
            bright = bright or 255
            while bright > 0:
                self.change_color(**start, brightness=bright, mode='41')
                bright -= speed
        if stop:
            bright = bright or 0
            while bright < 255:
                self.change_color(**stop, brightness=bright, mode='41')
                bright += speed

    def fade_sunlight(self, speed: int = 1) -> None:
        self.fade(stop=calc_sunlight(), speed=speed)

    def off(self):
        self.change_color(white=0)

    def on(self):
        self.change_color(white=255)


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit('Nope')
    colors = list(map(lambda x: int(x), sys.argv[2:]))
    print(colors)
    b = Bulb(sys.argv[1])
    b.change_color(*colors)


@socketio.on('change color')
@ws_login_required
def request_change_color(message):
    """
    Change the bulb's color.
    """
    emit('push color', {"device": message['device'], "color": message['color']},
         broadcast=True)
    device = get_device(message['device'])
    device.dev.change_color(*utils.RGBfromhex(message['color']),
                            utils.num(message.get('white', 0)), message.get('bright', 100), '41'
                            )


@socketio.on('outmap')
@ws_login_required
def reset_color_preview(message):
    """
    Reset the color preview
    """
    emit('preview reset', message['color'], broadcast=True)
