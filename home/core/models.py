"""
models.py
~~~~~~~~~

Contains classes to represent objects created by the parser.
"""
import importlib
import sys
import yaml

# from home.iot import *

# To be populated by the parser
drivers = []
devices = []
interfaces = {}
actions = []


class YAMLConfigParseError(Exception):
    pass


class DriverNotInstalledError(YAMLConfigParseError):
    pass


class DriverNotFoundError(YAMLConfigParseError):
    pass


def class_from_name(module_name, class_name):
    try:
        return getattr(importlib.import_module(
            'home.iot.' + module_name),
            class_name
        )
    except ImportError:
        raise DriverNotFoundError()


def method_from_name(klass, method_name):
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


class YAMLObject(yaml.YAMLObject):
    def __setstate__(self, kwargs):
        self.__init__(**kwargs)

    def __repr__(self):
        return self.name


class Device(YAMLObject):
    yaml_tag = '!device'

    def __init__(self, name, driver, config=None, key=None, group=None):
        self.name = name
        self.key = key
        self.driver = get_driver(driver)
        self.group = group
        if driver not in drivers:
            raise DriverNotInstalledError()
        # retrieve the class for driver
        dev = self.driver.klass
        if config:
            config_d = {}
            for d in config:
                config_d.update(d)
            self.dev = dev(**config_d)
        else:
            self.dev = dev()


class Driver(YAMLObject):
    yaml_tag = '!driver'

    def __init__(self, name, module, klass, interface=None):
        self.name = name
        self.interface = interface
        self.klass = class_from_name(module, klass)


class Action(YAMLObject):
    yaml_tag = '!action'

    def __init__(self, name, devices=[]):
        self.name = name
        self.devices = devices

    def run(self):
        for config in self.devices:
            dev = get_device(config['name'])
            method = method_from_name(dev.dev, config['method'])
            method()


class Interface(YAMLObject):
    yaml_tag = '!interface'

    def __init__(self, name, template):
        self.name = name
        interfaces[name] = template


yaml.add_path_resolver('!device', ['Device'], dict)
yaml.add_path_resolver('!action', ['ActionGroup'], dict)
yaml.add_path_resolver('!interface', ['Interface'], dict)
