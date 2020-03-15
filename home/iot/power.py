from abc import ABC, abstractmethod
from datetime import datetime, timedelta

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
        if datetime.now(sun[sun_state].tzinfo) >= sun[sun_state] + timedelta(seconds=offset):
            {'on': self.on,
             'off': self.off}[action]()

    @abstractmethod
    def power(self, on: bool):
        pass
