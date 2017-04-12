from home.core.models import get_device

message = "Good {}, {}. Today is {}, {} {}. The weather outside is currently {} degrees and {}. Later, " \
          "it will be {} degrees and {}. {}"


class Speech:
    def __init__(self, name, weather):
        self.name = name
        self.weather = get_device(weather).dev


def part_of_day(dt):
    if dt.hour < 12:
        return 'morning'
    if dt.hour < 17:
        return 'afternoon'
    if dt.hour < 19:
        return 'evening'
    return 'night'
