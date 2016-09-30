"""
utils.py
~~~~~~~~

This module contains various utilities.
"""
import importlib
import re

from home.core.models import DriverNotFoundError, devices, actions, drivers


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
        raise DriverNotFoundError()


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


def get_device_by_key(key):
    return next(device for device in devices if device.key == key)


def get_device(name):
    return next(device for device in devices if device.name == name)


def get_devices_by_group(group_name):
    return (device for device in devices if device.group == group_name)


def get_action(action_name):
    return next(action for action in actions if action.name == action_name)


def get_driver(driver_name):
    return next(driver for driver in drivers if driver == driver_name)