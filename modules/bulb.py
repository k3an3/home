#!/usr/bin/env python3
"""
bulb.py
~~~~~~~

This module is for communicating with the MagicHome LED bulb over the network.
"""
import socket
import sys

DEFAULT_BULB_HOST = '10.10.123.3'

prepare_hex = lambda x: format(x, 'x').zfill(2)

class Bulb:
    """
    A class representing a single MagicHome LED Bulb.
    """
    def __init__(self, host=DEFAULT_BULB_HOST):
        self.host = host

    def change_color(self, red=0, green=0, blue=0, brightness=100):
        """
        Provided RGB values and a brightness, change the color of the
        bulb with a TCP socket.
        """
        red *= int(brightness / 100)
        green *= int(brightness / 100)
        blue *= int(brightness / 100)
        print(red, green, blue)
        color_hex = prepare_hex(red) + prepare_hex(green) + prepare_hex(blue)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, 5577))
        data = bytearray.fromhex('31' + color_hex
                                + '00f00f')
        data.append(sum(data) % 256)
        s.send(data)


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit('Nope')
    colors = list(map(lambda x: int(x), sys.argv[1:]))
    print(colors)
    b = Bulb()
    b.change_color(*colors)
