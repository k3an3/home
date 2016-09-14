import yaml

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


class Device(yaml.YAMLObject):
    yaml_tag = '!device'

    def __init__(self, name, category, driver):
        if category not in DEVICE_CATEGORIES:
            raise InvalidDeviceCategoryError()
        self.name = name
        self.category = category
        self.driver = driver


class Sensor(yaml.YAMLObject):
    yaml_tag = '!sensor'

    def __init__(self, name, typeof, key, actions=[]):
        if typeof not in SENSOR_TYPES:
            raise InvalidSensorTypeException()
        self.name = name
        self.typeof = typeof
        self.key = key
        self.actions = actions


class ActionGroup(yaml.YAMLObject):
    yaml_tag = '!action'

    def __init__(self, name, devices=[]):
        self.name = name
        self.devices = devices


yaml.add_path_resolver('!device', ['Device'], dict)
yaml.add_path_resolver('!sensor', ['Sensor'], dict)
yaml.add_path_resolver('!action', ['ActionGroup'], dict)
