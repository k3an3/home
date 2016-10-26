#!/usr/bin/env python3
"""
bulb.py
~~~~~~~

This module is for communicating with the MagicHome LED bulb over the network.

Wire protocol:
8 bytes

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

DEFAULT_BULB_HOST = '172.16.42.201'

prepare_hex = lambda x: format(x, 'x').zfill(2)


class Bulb:
    """
    A class representing a single MagicHome LED Bulb.
    """
    def __init__(self, host=DEFAULT_BULB_HOST):
        self.host = host

    def change_color(self, red=0, green=0, blue=0, white=0, brightness=100):
        """
        Provided RGB values and a brightness, change the color of the
        bulb with a TCP socket.
        """
        red = int(red * brightness / 100)
        green = int(green * brightness / 100)
        blue = int(blue * brightness / 100)
        white = int(white * brightness / 100)
        color_hex = prepare_hex(red) + prepare_hex(green) + prepare_hex(blue)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.host, 5577))
            data = bytearray.fromhex('31' + color_hex
                                     + prepare_hex(white) + '0f0f')
            data.append(sum(data) % 256)
            s.send(data)
        except Exception:
            pass


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit('Nope')
    colors = list(map(lambda x: int(x), sys.argv[1:]))
    print(colors)
    b = Bulb()
    b.change_color(*colors)
