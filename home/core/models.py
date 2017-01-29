"""
models.py
~~~~~~~~~

Contains classes to represent objects created by the parser.
"""

import yaml

from home.core.utils import class_from_name, method_from_name, random_string

drivers = []
devices = []
interfaces = []
actions = []


def get_device_by_key(key):
    return next(device for device in devices if device.key == key)


def get_device_by_uuid(uuid):
    return next(device for device in devices if device.uuid == uuid)


def get_device(name):
    return next(device for device in devices if device.name == name)


def get_devices_by_group(group_name):
    return (device for device in devices if device.group == group_name)


def get_action(action_name):
    return next(action for action in actions if action.name == action_name)


def get_driver(driver_name):
    return next(driver for driver in drivers if driver.name == driver_name)


def get_interface(interface_name):
    return next(interface for interface in interfaces if interface.name == interface_name)


class YAMLConfigParseError(Exception):
    pass


class DriverNotInstalledError(YAMLConfigParseError):
    pass


class DriverNotFoundError(YAMLConfigParseError):
    pass


class DeviceNotFoundError(YAMLConfigParseError):
    pass


class YAMLObject(yaml.YAMLObject):
    def __setstate__(self, kwargs):
        self.__init__(**kwargs)

    def __repr__(self):
        return self.name


class Device(YAMLObject):
    yaml_tag = '!device'

    def __init__(self, name, driver=None, config=None, key=None, group=None):
        self.name = name
        self.key = key
        self.driver = driver
        self.group = group
        self.config = config
        self.uuid = random_string()
        self.dev = None

    def setup(self):
        # retrieve the class for driver
        if self.driver:
            self.driver = get_driver(self.driver)
            dev = self.driver.klass
            if self.config:
                config_d = {}
                for d in self.config:
                    config_d.update(d)
            self.dev = dev(**config_d)


class Driver(YAMLObject):
    yaml_tag = '!driver'

    def __init__(self, name, module, klass, interface=None):
        self.name = name
        self.interface = interface
        self.klass = class_from_name(module, klass)

    def setup(self):
        if self.interface:
            self.interface = get_interface(self.interface)


class Action(YAMLObject):
    yaml_tag = '!action'

    def __init__(self, name, devices=[]):
        self.name = name
        self.devices = devices

    def run(self):
        for config in self.devices:
            dev = get_device(config['name'])
            method = method_from_name(dev.dev, config['method'])
            try:
                if config.get('config'):
                    method(**config['config'])
                else:
                    method()
            except Exception as e:
                print("Action:", str(e))


class Interface(YAMLObject):
    yaml_tag = '!interface'

    def __init__(self, name, friendly_name, template):
        self.name = name
        self.friendly_name = friendly_name
        self.template = template


yaml.add_path_resolver('!device', ['Device'], dict)
yaml.add_path_resolver('!action', ['ActionGroup'], dict)
yaml.add_path_resolver('!interface', ['Interface'], dict)
