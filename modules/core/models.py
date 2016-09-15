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
installed_devices = {}
installed_sensors = {}
devices = []
sensors = []

DEVICE_CATEGORIES = (
    'bulb', 'led', 'lock', 'outlet',
)

SENSOR_TYPES = (
    'door', 'camera', 'other',
)

class YAMLConfigParseError(Exception):
    pass


class InvalidDeviceError(YAMLConfigParseError):
    pass


class InvalidSensorError(YAMLConfigParseError):
    pass


class InvalidDriverError(YAMLConfigParseError):
    pass


def class_from_name(module_name, class_name):
    return getattr(importlib.import_module(
        'modules.iot.' + module_name),
        class_name
        )


class YAMLObject(yaml.YAMLObject):
    def __setstate__(self, kwargs):
        self.__init__(**kwargs)

    def __repr__(self):
        return self.name


class Device(YAMLObject):
    yaml_tag = '!device'

    def __init__(self, name, driver, config=None):
        self.name = name
        if driver not in installed_devices:
            raise InvalidDeviceError()
        # retreive the class for driver
        driver = installed_devices[driver]
        if config:
            config_d = {}
            for d in config:
                config_d.update(d)
            self.driver = driver(**config_d)
        else:
            self.driver = driver()


class Sensor(YAMLObject):
    yaml_tag = '!sensor'

    def __init__(self, name, driver, key, config=None, actions=[]):
        self.name = name
        self.actions = actions
        self.key = key
        if driver not in installed_sensors:
            raise InvalidSensorError()
        # retreive the class for driver
        driver = installed_sensors[driver]
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
        if typeof == 'device':
            installed_devices[name] =  class_from_name(module, klass)
        elif typeof == 'sensor':
            installed_sensors[name] =  class_from_name(module, klass)
        else:
            raise InvalidDriverTypeError()


class ActionGroup(yaml.YAMLObject):
    yaml_tag = '!action'

    def __init__(self, name, devices=[]):
        self.name = name
        self.devices = devices


yaml.add_path_resolver('!device', ['Device'], dict)
yaml.add_path_resolver('!sensor', ['Sensor'], dict)
yaml.add_path_resolver('!action', ['ActionGroup'], dict)
