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
from datetime import datetime

from astral import Astral

from home import config
from home.core.utils import num

SUPPORTED_MODES = ['31', '41', '61']
SUPPORTED_FUNCTIONS = list(range(25, 39))
TAIL = '0f'

prepare_hex = lambda x: format(x, 'x').zfill(2)


class Bulb:
    """
    A class representing a single MagicHome LED Bulb.
    """

    def __init__(self, host):
        self.host = host

    def change_color(self, red=0, green=0, blue=0, white=0, brightness=100, mode='31', function=None, speed='1f'):
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
            red = num(red * brightness / 100)
            green = num(green * brightness / 100)
            blue = num(blue * brightness / 100)
            white = num(white * brightness / 100)
            color_hex = (prepare_hex(red) + prepare_hex(green) + prepare_hex(blue)
                         + prepare_hex(white))
            if white:
                color_mode = '0f'
            else:
                color_mode = 'f0'
            # Build packet
            data = bytearray.fromhex(mode + color_hex
                                     + color_mode + TAIL)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # TCP port 5577
            s.connect((self.host, 5577))
            # Compute checksum
            data.append(sum(data) % 256)
            s.send(data)
        except Exception:
            pass

    def sunlight(self):
        """
        Calculate an appropriate brightness for the bulb depending on
        current sunlight.
        :return: White brightness
        """
        a = Astral()
        a.solar_depression = 'civil'
        city = a[config.LOCATION]
        sun = city.sun(date=datetime.now(), local=True)
        if datetime.now() < sun['sunrise']:
            white = 255 - (datetime.now() - sun['sunrise']) * 200 / 6
        elif datetime.now() > sun['sunset']:
            white = 255 - (datetime.now() - sun['sunset']) * 200 / 6
        self.change_color(white=white)


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit('Nope')
    colors = list(map(lambda x: int(x), sys.argv[1:]))
    print(colors)
    b = Bulb()
    b.change_color(*colors)
