"""
models.py
~~~~~~~~~

Contains classes to represent objects created by the parser.
"""
import yaml

from home.core.utils import class_from_name, method_from_name, get_device, get_driver

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
