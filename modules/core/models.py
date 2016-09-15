import importlib
import sys
import yaml

#from modules.iot import *

DEVICE_CATEGORIES = (
    'bulb', 'led', 'lock', 'outlet',
)

SENSOR_TYPES = (
    'door', 'camera', 'other',
)

class YAMLConfigParseError(Exception):
    pass


class InvalidDeviceCategoryError(YAMLConfigParseError):
    pass


class InvalidSensorTypeYAMLConfigParseError(YAMLConfigParseError):
    pass


def class_from_name(name):
    name = name.split('.')
    return getattr(importlib.import_module(
        'modules.iot.' + name[0]),
        name[1]
        )


class Device(yaml.YAMLObject):
    yaml_tag = '!device'

    def __init__(self, name, driver, config):
        self.name = name
        self.driver = class_from_name(driver)

    def __setstate__(self, args):
        self.__init__(**args)

    def __repr__(self):
        return self.name


class Sensor(yaml.YAMLObject):
    yaml_tag = '!sensor'

    def __init__(self, name, typeof, key, actions=[]):
        if typeof not in SENSOR_TYPES:
            raise InvalidSensorTypeException()
        self.name = name
        self.typeof = typeof
        self.key = key
        self.actions = actions

    def __repr__(self):
        return self.name


class ActionGroup(yaml.YAMLObject):
    yaml_tag = '!action'

    def __init__(self, name, devices=[]):
        self.name = name
        self.devices = devices


yaml.add_path_resolver('!device', ['Device'], dict)
yaml.add_path_resolver('!sensor', ['Sensor'], dict)
yaml.add_path_resolver('!action', ['ActionGroup'], dict)
