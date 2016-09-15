"""
models.py
~~~~~~~~~

Contains classes to represent objects created by the parser.
"""
import importlib
import sys
import yaml

#from modules.iot import *

# To be populated by the parser
drivers = {}
devices = []


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
        if driver not in drivers:
            raise DeviceNotInstalledError()
        # retreive the class for driver
        driver = drivers[driver]
        if config:
            config_d = {}
            for d in config:
                config_d.update(d)
            self.driver = driver(**config_d)
        else:
            self.driver = driver()


class Driver(YAMLObject):
    yaml_tag = '!driver'

    def __init__(self, typeof, name, module, klass):
        self.name = name
        drivers[name] =  class_from_name(module, klass)


class ActionGroup(yaml.YAMLObject):
    yaml_tag = '!action'

    def __init__(self, name, devices=[]):
        self.name = name
        self.devices = devices


yaml.add_path_resolver('!device', ['Device'], dict)
yaml.add_path_resolver('!action', ['ActionGroup'], dict)
