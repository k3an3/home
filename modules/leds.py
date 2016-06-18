#!/usr/bin/env python3
"""
leds.py
~~~~~~~

Module to handle 4 RGBW LEDs and 5-pin RGBW LED strips.

Requires gpiozero and a Raspberry Pi

Default outputs (determined arbitrarily):
4  - red
17 - green
22 - blue
18 - white
"""
import sys

from gpiozero import RGBLED, LED

class LEDstrip:
    """
    A class representing a 5-pin RGBW LED strip.
    """
    def __init__(self, red=4, green=17, blue=22, white=18):
        """
        Initializer with default pins for each color.
        """
        # This next line requires a version of gpiozero newer than
        # May 8 2016, which was when the pwm kwarg was added.
        # Without this parameter, it will complain about the pins
        # not supporting pwm.
        self.rgb = RGBLED(red=red, green=green, blue=blue, pwm=False)
        self.white = LED(white)

    def change_color(self, red=0, green=0, blue=0, white=0):
        """
        Given RGBW values, changes the color of the LEDs.
        """
        self.rgb.color = (red / 255, green / 255 , blue / 255)
        self.white = white / 255


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit('Nope')
    colors = list(map(lambda x: int(x), sys.argv[1:]))
    print(colors)
    l = LEDstrip()
    l.change_color(*colors)
