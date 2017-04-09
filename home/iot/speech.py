from home.core.models import get_device

message = "Good morning, {}. Today is {}, {} {}. The weather outside is currently {} degrees and {}. Later, " \
          "it will be {} degrees and {}. "


class Speech:
    def __init__(self, name, weather):
        self.name = name
        self.weather = get_device(weather).dev
