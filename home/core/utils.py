"""
utils.py
~~~~~~~~

This module contains various utilities.
"""
import re

def num(n):
    """
    Given a string, attempt to convert to int.
    """
    try:
        n = int(n)
    except ValueError:
        n = 0
    return n

def RGBfromhex(color_hex):
    """
    Given a string in the format '#xxxxxx', where '#' is optional and
    'xxxxxx' represents 3 hexadecimal bytes, convert to RGB integer
    values between 0 and 255. Return all zeros if input is invalid.
    """
    red = 0
    green = 0
    blue = 0
    if re.match('^#?[A-Fa-f0-9]{6}$', color_hex):
        color_hex = color_hex.replace('#', '')
        red = int(color_hex[0:2], 16)
        green = int(color_hex[2:4], 16)
        blue = int(color_hex[4:6], 16)
    return red, green, blue
