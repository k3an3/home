"""
models.py
~~~~~~~~~

Contains classes to represent objects created by the parser.
"""
import os
from copy import deepcopy
from multiprocessing import Process
from time import sleep
from typing import Iterator, Dict, List, Callable
from uuid import uuid4

import yaml

from home.core.tasks import scheduler, multiprocessing_run, run
from home.core.utils import class_from_name, method_from_name, random_string
from home.settings import TEMPLATE_DIR

drivers = []
devices = {}
devices_by_uuid = {}
interfaces = []
actions = []
widgets = {}
displays = []


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

    def __init__(self, name: str, driver: str = None, config: Dict = None, group: str = None, widget: bool = True):
        self.name = name
        self.driver = driver
        self.group = group
        self.config = config
        self.uuid = str(uuid4())
        self.dev = None
        self.last_task = None
        self.widget = widget

    def setup(self) -> None:
        """
        Set up the driver that this device will use
        """
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
                raise DeviceSetupError("Failed to configure device '" + self.name + "': " + str(e))
            if self.widget and hasattr(self.dev, 'widget'):
                self.build_widget(self.dev.widget)
                widgets.update(self.widget['mapping'])
            if hasattr(self.dev, 'actions'):
                ta = deepcopy(self.dev.actions)
                for action in ta:
                    for d in action['devices']:
                        d['name'] = self.name
                    a = Action(name=action['name'] + " " + self.name, devices=action['devices'])
                    a.setup()
                    a.group = self.group
                    actions.append(a)

    def build_widget(self, config: Dict) -> str:
        mapping = {}
        html = '<div class="widget-panel panel panel-primary"><div class="panel-heading"><h3 class="panel-title">{' \
               '} ({})</h3></div><div class="panel-body">'.format(self.name, self.driver)
        html += '<div class="device-status" id="status-{}"></div>'.format(self.name.replace(' ', '-'))
        buttons = config.get('buttons')
        if len(buttons) > 1:
            html += '<div class="btn-group" role="group" aria-label="...">'
        for button in buttons:
            if not button.get('method') and not button.get('action'):
                raise WidgetSetupError('Widget must have at least a method or action defined')
            _id = random_string(6)
            html += '<button class="widget btn {_class}" id="{id}">{text}</button>'.format(
                _class=button.get('class', 'btn-primary'),
                id=_id,
                text=button.get('text', _id)
            )
            mapping[_id] = ('method' if button.get('method') else 'action',
                            method_from_name(self.dev, button.get('method')) if button.get('method')
                            else button.get('action') + " " + self.name, button.get('config', {}), self)
        if len(buttons) > 1:
            html += '</div>'
        html += '</div></div>'
        self.widget = {'html': html, 'mapping': mapping}


class MultiDevice(YAMLObject):
    yaml_tag = '!multidevice'

    def __init__(self, name: str, devices: List, widget: bool = True):
        self.name = name
        self.devices = devices
        self.widget = widget
        self.group = None

    def __getattr__(self, name):
        if name == 'driver':
            return self.devices[0].driver
        elif name == 'driver.noserialize':
            return True
        elif name == 'widget':
            return self.widget
        elif name == 'dev':
            #return self.devices[0].dev
            return self

        def method(*args, **kwargs):
            for device in self.devices:
                method = method_from_name(device.dev, name)
                method(*args, **kwargs)

        return method

    def setup(self):
        for device in self.devices:
            device.widget = self.widget
            device.setup()
        if self.widget:
            self.widget = self.devices[0].widget
            for key in self.widget['mapping']:
                _map = self.widget['mapping'][key]
                self.widget['mapping'][key] = (_map[0], method_from_name(self, _map[1].__name__), _map[2], self)
            widgets.update(self.widget['mapping'])
            self.widget['html'] = self.widget['html'].replace(self.devices[0].name, self.name)
            self.widget['html'] = self.widget['html'].replace('status-' + self.name, 'status-' + self.name.replace(' ', '_'))


class Driver(YAMLObject):
    """
    Represents the driver for a type of device.
    """
    yaml_tag = '!driver'

    def __init__(self, module: str, klass: str, name: str = None, interface: str = None, noserialize: bool = False,
                 static: bool = False):
        self.name = name or klass.lower()
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
            devices[self.name] = dev


class Action(YAMLObject):
    """
    Executes one or more actions when triggered.
    """
    yaml_tag = '!action'

    def __init__(self, name, devices: List = [], actions: List = [], jitter: int = 0, button: str = 'btn-info'):
        self.name = name
        self.devices = []
        self.actions = []
        self.subscriptions = []
        self.devs = devices
        self.acts = actions
        self.jitter = jitter
        self.button = button

    def setup(self) -> None:
        for dev in self.devs:
            try:
                self.devices.append((get_device(dev['name']), dev))
            except StopIteration:
                raise DeviceNotFoundError(
                    "Failed to configure action " + self.name + ": Can't find device " + dev['name'])
        for act in self.acts:
            if act == self.name:
                raise ActionSetupError(
                    "Failed to configure action " + self.name + ": Action can't call itself"
                )
            try:
                self.actions.append(get_action(act))
            except StopIteration:
                raise ActionSetupError(
                    "Failed to configure action " + self.name + ": Can't find action " + act)
        if self.button:
            widgets.update({self.name: ('action', self.name, None, self)})

    def prerun(self) -> (Iterator[Process], Iterator[int]):
        for action in self.actions:
            action.run()
        for callback, args, kwargs in self.subscriptions:
            callback(*args, **kwargs)
        for device, config in self.devices:
            method = method_from_name(device.dev, config['method'])
            kwargs = config.get('config', {})
            print("Execute action", config['method'])
            if device.driver.noserialize or type(device) is MultiDevice:
                multiprocessing_run(target=method, delay=config.get('delay', 0), **kwargs)
                continue
            try:
                yield device, method, config.get('delay', 0), kwargs
            except Exception as e:
                print("Error", e)

    def run(self, jitter: bool = False):
        if self.jitter and jitter:
            sleep(self.jitter)
        for device, method, delay, kwargs in self.prerun():
            device.last_task = run(method, delay=delay, **kwargs)


class Interface(YAMLObject):
    """
    Represents an HTML frontend to control a device.
    """
    yaml_tag = '!interface'

    def __init__(self, name: str, friendly_name: str = None, template: str = None, public: bool = False):
        self.name = name
        self.friendly_name = friendly_name or name.title()
        self.template = os.path.join(TEMPLATE_DIR, template or name + ".html")
        self.public = public


class Display(YAMLObject):
    """
    Represents a display panel, perhaps wall mounted, that always displays a dashboard.
    """
    yaml_tag = '!display'

    def __init__(self, name: str, widgets: List[Dict] = [], controls: bool = True, template: str = ""):
        self.name = name
        self.widgets = widgets
        self.controls = controls
        self.template = template

    def render(self) -> str:
        html = []
        for w in self.widgets:
            dev = get_device(w['device'])
            config = w.get('config', {})
            html.append(dev.dev.render_widget(**config))
        return html


# Set up YAML object instantiation
yaml.add_path_resolver('!device', ['Device'], dict)
yaml.add_path_resolver('!multidevice', ['MultiDevice'], dict)
yaml.add_path_resolver('!action', ['ActionGroup'], dict)
yaml.add_path_resolver('!interface', ['Interface'], dict)
yaml.add_path_resolver('!display', ['Display'], dict)


def add_scheduled_job(job: Dict):
    if job.get('action'):
        scheduler.add_job(get_action(job.pop('action')).run,
                          trigger=job.pop('trigger', 'cron'),
                          kwargs=dict(jitter=True), **job)
    elif job.get('device'):
        device = get_device(job.pop('device'))
        method = method_from_name(device.dev, job.pop('method'))
        scheduler.add_job(method, trigger=job.pop('trigger', 'cron'), kwargs=job.pop('config', {}), **job)


def get(name: str, search: List):
    try:
        return next(_ for _ in search if _.name == name)
    except StopIteration:
        raise StopIteration("Couldn't find " + name + " in " + str(search))


def get_device_by_uuid(uuid: str) -> Device:
    return devices_by_uuid[uuid]


def get_device(name: str) -> Device:
    return devices[name]


def get_devices_by_group(group_name: str) -> Iterator[Device]:
    return (device for device in devices.values() if device.group == group_name)


def get_action(action_name: str) -> Action:
    return next(action for action in actions if action.name.lower() == action_name.lower())


def get_driver(driver_name: str) -> Driver:
    return get(driver_name, drivers)


def get_interface(interface_name: str) -> Interface:
    return get(interface_name, interfaces)


def get_display(display_name: str) -> Display:
    return get(display_name, displays)


def subscribe_to_action(action_name: str, callback: Callable, *args, **kwargs):
    action = get_action(action_name)
    action.subscriptions.append((callback, args, kwargs))


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


class WidgetSetupError(YAMLConfigParseError):
    pass
