#!/usr/bin/env python3
import socket
import sys

def change_color(red, green, blue, brightness=100):
    red *= int(brightness / 100)
    green *= int(brightness / 100)
    blue *= int(brightness / 100)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('172.24.1.248', 5577))
    for i in range(0, 255):
        data = bytearray.fromhex('31' + format(red, 'x').zfill(2)
                                + format(green, 'x').zfill(2)
                                + format(blue, 'x').zfill(2)
                                + '00f00f' + format(i, 'x').zfill(2))
        s.send(data)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit('Nope')
    colors = list(map(lambda x: int(x), sys.argv[1:]))
    print(colors)
    change_color(*colors)