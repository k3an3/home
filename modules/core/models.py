"""
models.py
~~~~~~~~~

Contains classes to represent objects created by the parser.
"""
import importlib
import sys
import yaml

# from modules.iot import *

# To be populated by the parser
drivers = {}
devices = []
interfaces = {}


class YAMLConfigParseError(Exception):
    pass


class DriverNotInstalledError(YAMLConfigParseError):
    pass


class DriverNotFoundError(YAMLConfigParseError):
    pass


def class_from_name(module_name, class_name):
    try:
        return getattr(importlib.import_module(
            'modules.iot.' + module_name),
            class_name
            )
    except ImportError:
        raise DriverNotFoundError()


def get_device_by_key(key):
    return next(device for device in devices if device.key == key)


class YAMLObject(yaml.YAMLObject):
    def __setstate__(self, kwargs):
        self.__init__(**kwargs)

    def __repr__(self):
        return self.name


class Device(YAMLObject):
    yaml_tag = '!device'

    def __init__(self, name, driver, config=None, key=None):
        self.name = name
        self.key = key
        self.driver = driver
        if driver not in drivers:
            raise DriverNotInstalledError()
        # retrieve the class for driver
        dev = drivers[driver]
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
        drivers[name] = class_from_name(module, klass)


class ActionGroup(YAMLObject):
    yaml_tag = '!action'

    def __init__(self, name, devices2=[]):
        self.name = name
        self.devices = devices2


class Interface(YAMLObject):
    yaml_tag = '!interface'

    def __init__(self, name, template):
        interfaces[name] = template


yaml.add_path_resolver('!device', ['Device'], dict)
yaml.add_path_resolver('!action', ['ActionGroup'], dict)
yaml.add_path_resolver('!interface', ['Interface'], dict)
