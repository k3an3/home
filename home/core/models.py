"""
models.py
~~~~~~~~~

Contains classes to represent objects created by the parser.
"""
from multiprocessing import Process
from typing import Iterator

import yaml

from home.core.celery import _run
from home.core.utils import class_from_name, method_from_name, random_string

# Arrays to store object instances
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


class DeviceSetupError(YAMLConfigParseError):
    pass


class YAMLObject(yaml.YAMLObject):
    """
    Base class for YAML objects, simply to print the correct name
    """

    def __setstate__(self, kwargs):
        self.__init__(**kwargs)

    def __repr__(self):
        return self.name


class Device(YAMLObject):
    """
    Representation of a specific physical instance of a driver.
    """
    yaml_tag = '!device'

    def __init__(self, name, driver=None, config=None, key=None, group=None):
        self.name = name
        self.key = key  # deprecated?
        self.driver = driver
        self.group = group
        self.config = config
        self.uuid = random_string()
        self.dev = None
        self.last_method = None
        self.last_kwargs = {}

    def setup(self) -> None:
        """
        Set up the driver that this device will use
        """
        # retrieve the class for driver
        if self.driver:
            self.driver = get_driver(self.driver)
            dev = self.driver.klass
            config_d = self.config if self.config else {}
            try:
                self.dev = dev(**config_d)
            except Exception as e:
                raise DeviceSetupError("Failed to configure device '" + self.name + "'")


class Driver(YAMLObject):
    """
    Represents the driver for a type of device.
    """
    yaml_tag = '!driver'

    def __init__(self, module, klass, name=None, interface=None):
        self.name = name or module
        self.interface = interface
        self.klass = class_from_name(module, klass)

    def setup(self) -> None:
        """
        Set up frontend, if it exists
        """
        if self.interface:
            self.interface = get_interface(self.interface)


class Action(YAMLObject):
    """
    Executes one or more actions when triggered.
    """
    yaml_tag = '!action'

    def __init__(self, name, devices=[]):
        self.name = name
        self.devices = []
        self.devs = devices

    def setup(self) -> None:
        for dev in self.devs:
            self.devices.append((get_device(dev['name']), dev))

    def prerun(self) -> (Iterator[Process], Iterator[int]):
        for device, config in self.devices:
            if config['method'] == 'last':
                method = method_from_name(device.dev, device.last_method)
                kwargs = device.last_kwargs
            else:
                method = method_from_name(device.dev, config['method'])
                kwargs = config.get('config', {})
                device.last_method = method
                device.last_kwargs = kwargs
            print("Execute action", config['method'])
            try:
                yield method, config.get('delay', 0), kwargs
            except Exception as e:
                print("Error", e)

    def run(self):
        for method, delay, kwargs in self.prerun():
            kwargs['method'] = method
            _run.apply_async(kwargs=kwargs, countdown=delay)


class Interface(YAMLObject):
    """
    Represents an HTML frontend to control a device.
    """
    yaml_tag = '!interface'

    def __init__(self, name, friendly_name, template):
        self.name = name
        self.friendly_name = friendly_name
        self.template = template


# Set up YAML object instantiation
yaml.add_path_resolver('!device', ['Device'], dict)
yaml.add_path_resolver('!action', ['ActionGroup'], dict)
yaml.add_path_resolver('!interface', ['Interface'], dict)
