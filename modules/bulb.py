#!/usr/bin/env python3
import socket
import sys

prepare_hex = lambda x: format(x, 'x').zfill(2)

def change_color(red=0, green=0, blue=0, brightness=100, color_hex=None):
    if not color_hex:
        red *= int(brightness / 100)
        green *= int(brightness / 100)
        blue *= int(brightness / 100)
        color_hex = prepare_hex(red) + prepare_hex(green) + prepare_hex(blue)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('10.10.123.3', 5577))
    data = bytearray.fromhex('31' + color_hex
                            + '00f00f')
    data.append(sum(data) % 256)
    s.send(data)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit('Nope')
    colors = list(map(lambda x: int(x), sys.argv[1:]))
    print(colors)
    change_color(*colors)
