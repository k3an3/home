import calendar
import random

import datetime
import requests
from flask import request, abort

from home.core.models import get_device
from home.iot.speech import Speech, message, part_of_day
from home.web.utils import api_auth_required
from home.web.web import app

BASE_URL = "http://api.openweathermap.org/data/2.5/"

RAINY_SAYINGS = (
    "it's going to be a wet one.",
    "I hope you saved something for a rainy day.",
    "you might just get wet.",
    "unless you want to get wet.",
)

WINDY_SAYINGS = (
    "Hold on to your hat! It's going to be a breezy one.",
    "Batten down the hatches! It may get windy.",
    "Watch out for falling trees on this windy day!",
    "The wind might just blow you over today.",
)

HOT_SAYINGS = (
    "Drop your socks and grab your crocs! It's going to be a hot one.",
    "Might want to stay inside, or go to the pool. It will be a bit hot.",
    "Soak up that air conditioning! It's hot out.",
    "Make sure to stay hydrated in this hot weather!",
    "Spend some quality time inside today, it'll be hot out there.",
)

COLD_SAYINGS = (
    "It might be a hat and glove kind of day.",
    "Try to keep warm!",
    "The weather outside is frightful, but the inside is pretty darn nice.",
    "Break out the handwarmers! It may be hard to type.",
    "Crank up the heater and get toasty!",
    "Better put another log on the fire, it is cold out!",
)

SNOWY_SAYINGS = (
    "Put on your snowshoes, you'll need them today.",
    "Gone away is the bluebird, here to stay is the new bird. a k a, it might be a winter wonderland out there.",
    "Don't go to Dairy Queen today, eat some snow instead!",
    "Might just be a good day for a snowball fight! Rally your troops.",
    "Just because it's snowing doesn't mean you get the day off.",
)

STORMY_SAYINGS = (
    "Stay away from doors and windows!",
    "You may want to seek shelter indoors today.",
    "Don't get struck by lightning!",
    "Thunder and lightning from above!",
)


class Weather:
    def __init__(self, api_key):
        self.api_key = api_key

    def get(self, city_id=None, zip=None, latlon=None, name=None, mode='weather'):
        if city_id:
            loc = "id=" + str(city_id)
        elif zip:
            loc = "zip=" + str(zip)
        elif latlon:
            loc = "lat={0[0]}&lon={0[1]}".format(latlon)
        elif name:
            loc = "q=" + name
        uri = '?{}&APPID={}&units=imperial'.format(loc, self.api_key)
        r = requests.get(BASE_URL + mode + uri)
        if not r.status_code == 200 or not 'json' in r.headers['content-type']:
            raise Exception("Invalid response from OpenWeatherMap")
        return Forecast(r.json())


class Forecast:
    def __init__(self, data: dict):
        if data.get('list'):
            data = data['list'][1]
        self.temp = data['main']['temp']
        self.description = data['weather'][0]['description']
        self.wind = data['wind']['speed']
        self.name = data.get('name')

    def windy(self) -> bool:
        return self.wind > 20

    def rainy(self) -> bool:
        return 'rain' in self.description.lower()

    def snowy(self) -> bool:
        return 'snow' in self.description.lower()

    def stormy(self) -> bool:
        return 'storm' in self.description.lower()


def get_quote() -> str:
    r = requests.get('https://quotes.rest/qod', headers={'Accept': 'application/json'})
    if r.status_code == 200:
        return r.json()['contents']['quotes'][0]['quote']


def format_weather(weather: Forecast, forecast: Forecast, speech: Speech) -> str:
    dt = datetime.datetime.now()
    extra = []
    if weather.windy() or forecast.windy():
        extra.append(random.choice(WINDY_SAYINGS))
    if weather.rainy() or forecast.rainy():
        extra.append("Don't forget to bring an umbrella, " + random.choice(RAINY_SAYINGS))
    if weather.snowy() or forecast.snowy():
        extra.append(random.choice(SNOWY_SAYINGS))
    if weather.temp > 90 or forecast.temp > 90:
        extra.append(random.choice(HOT_SAYINGS))
    if weather.temp < 28 or forecast.temp < 28:
        extra.append(random.choice(COLD_SAYINGS))
    extra.append(get_quote())
    return message.format(part_of_day(dt), speech.name,
                          calendar.day_name[dt.weekday()],
                          calendar.month_name[dt.month],
                          dt.day, weather.name, round(weather.temp),
                          weather.description,
                          round(forecast.temp),
                          forecast.description,
                          ' '.join(extra))


@app.route('/api/motd', methods=['GET', 'POST'])
@api_auth_required
def motd(client):
    try:
        speech = get_device(request.values.get('device'))
    except StopIteration:
        abort(404)
    if not speech.driver.klass == Speech:
        raise NotImplementedError
    if not client.has_permission(speech.group):
        abort(403)
    speech = speech.dev
    weather = speech.weather.get(latlon=request.values.get('loc').split(','))
    forecast = speech.weather.get(latlon=request.values.get('loc').split(','), mode='forecast')
    return format_weather(weather, forecast, speech)
