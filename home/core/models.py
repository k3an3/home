"""
models.py
~~~~~~~~~

Contains classes to represent objects created by the parser.
"""
import os
from multiprocessing import Process

import yaml
from typing import Iterator, Dict, List

from home.core.async import run as queue_run, scheduler
from home.core.utils import class_from_name, method_from_name, random_string

# Arrays to store object instances
from home.settings import TEMPLATE_DIR

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


class DuplicateDeviceNameError(YAMLConfigParseError):
    pass


class ActionSetupError(YAMLConfigParseError):
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

    def __init__(self, name: str, driver: str = None, config: Dict = None, key: str = None, group: str = None):
        self.name = name
        self.key = key  # deprecated?
        self.driver = driver
        self.group = group
        self.config = config
        self.uuid = random_string()
        self.dev = None
        self.last_method = None
        self.last_kwargs = {}
        self.last_task = None

    def setup(self) -> None:
        """
        Set up the driver that this device will use
        """
        if len([device for device in devices if device.name == self.name]) > 1:
            raise DuplicateDeviceNameError(self.name)
        # retrieve the class for driver
        if self.driver:
            try:
                self.driver = get_driver(self.driver)
            except StopIteration:
                raise DriverNotInstalledError("Can't find driver " + str(self.driver)
                                              + " for device " + self.name)
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

    def __init__(self, module: str, klass: str, name: str = None, interface: str = None, noserialize: bool = False, static: bool = False):
        self.name = name or module
        self.interface = interface
        self.klass = class_from_name(module, klass)
        self.noserialize = noserialize
        self.static = static

    def setup(self) -> None:
        """
        Set up frontend, if it exists
        """
        if self.interface:
            self.interface = get_interface(self.interface)
        if self.static:
            dev = Device(self.name, self.name)
            dev.setup()
            devices.append(dev)


class Action(YAMLObject):
    """
    Executes one or more actions when triggered.
    """
    yaml_tag = '!action'

    def __init__(self, name, devices: List = [], actions: List = []):
        self.name = name
        self.devices = []
        self.actions = []
        self.devs = devices
        self.acts = actions

    def setup(self) -> None:
        for dev in self.devs:
            try:
                self.devices.append((get_device(dev['name']), dev))
            except StopIteration:
                raise DeviceNotFoundError(
                    "Failed to configure action " + self.name + ": Can't find device " + dev['name'])
        for act in self.acts:
            if act['name'] == self.name:
                raise ActionSetupError(
                    "Failed to configure action " + self.name + ": Action can't call itself"
                )
            try:
                self.actions.append((get_action(act['name']), act))
            except StopIteration:
                raise ActionSetupError(
                    "Failed to configure action " + self.name + ": Can't find action " + act['name'])

    def prerun(self) -> (Iterator[Process], Iterator[int]):
        for action in self.actions:
            action.run()
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
            if device.driver.noserialize:
                Process(target=method, kwargs=kwargs).start()
                continue
            try:
                yield device, method, config.get('delay', 0), kwargs
            except Exception as e:
                print("Error", e)

    def run(self):
        for device, method, delay, kwargs in self.prerun():
            device.last_task = queue_run(method, delay=delay, **kwargs)


class Interface(YAMLObject):
    """
    Represents an HTML frontend to control a device.
    """
    yaml_tag = '!interface'

    def __init__(self, name: str, friendly_name: str, template: str, public: bool = False):
        self.name = name
        self.friendly_name = friendly_name
        self.template = os.path.join(TEMPLATE_DIR, template)
        self.public = public


# Set up YAML object instantiation
yaml.add_path_resolver('!device', ['Device'], dict)
yaml.add_path_resolver('!action', ['ActionGroup'], dict)
yaml.add_path_resolver('!interface', ['Interface'], dict)


def add_scheduled_job(job):
    if job.get('action'):
        scheduler.add_job(get_action(job.pop('action')).run,
                          trigger=job.pop('trigger', 'cron'),
                          **job)
    elif job.get('device'):
        device = get_device(job.pop('device'))
        method = method_from_name(device.dev, job.pop('method'))
        scheduler.add_job(method, trigger=job.pop('trigger', 'cron'), kwargs=job.pop('config', {}), **job)
