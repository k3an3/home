"""
utils.py
~~~~~~~~

This module contains various utilities.
"""
import hashlib
import importlib
import os
import re
import subprocess
from datetime import datetime

from astral import Astral

from home import config


def num(n):
    """
    Given a string, attempt to convert to int. Otherwise, return 0.
    :param n: A string containing a number.
    :return: An integer representation of the provided value.
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
    :param color_hex: A color represented by hex values.
    :return: 3 integer values for RGB values.
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


def class_from_name(module_name, class_name):
    """
    Given a module name and class name, return a class.
    :param module_name: Module name to import.
    :param class_name: Class name to find in the module.
    :return: The class object.
    """
    try:
        return getattr(importlib.import_module(
            'home.iot.' + module_name),
            class_name
        )
    except ImportError:
        raise NotImplementedError()


def method_from_name(klass, method_name):
    """
    Given an imported class, return the given method pointer.
    :param klass: An imported class containing the method.
    :param method_name: The method name to find.
    :return: The method pointer
    """
    try:
        return getattr(klass, method_name)
    except AttributeError:
        raise NotImplementedError()


def sunlight():
    a = Astral()
    a.solar_depression = 'civil'
    city = a[config.LOCATION]
    sun = city.sun(date=datetime.now(), local=True)
    if datetime.now() < sun['sunrise']:
        return 255 * (datetime.now() - sun['sunrise']) / 6
    elif datetime.now() > sun['sunset']:
        return 255 * (datetime.now() - sun['sunset']) / 6


random_string = lambda: hashlib.sha1(os.urandom(128)).hexdigest()


def reload():
    subprocess.call(['sudo', 'systemctl', 'restart', 'home'])


def update():
    subprocess.call(['git', 'stash'])
    subprocess.call(['git', 'pull', 'origin', 'master'])
    subprocess.call(['git', 'stash', 'apply'])
    subprocess.call(['/srv/www/home/env/bin/pip', 'install', '-r', 'requirements.txt', '--upgrade'])
    reload()
