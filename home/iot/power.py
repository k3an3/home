from abc import ABC, abstractmethod
from datetime import datetime

from astral import Astral

from home import settings


class Power(ABC):
    def on(self):
        self.power(True)

    def off(self):
        self.power(False)

    def auto(self, action: str = 'on', sun_state: str = 'sunset', offset: int = 0):
        a = Astral()
        a.solar_depression = 'civil'
        city = a[settings.LOCATION]
        sun = city.sun(date=datetime.now(), local=True)
        sun_state_time = datetime.now(sun[sun_state].tzinfo)
        if datetime.now() >= sun_state_time + offset:
            {'on': self.on,
             'off': self.off}[action]()

    @abstractmethod
    def power(self, on: bool):
        if on:
            self.on()
        else:
            self.off()
