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
    "The wind might just blow you over."
)

HOT_SAYINGS = (
    "Drop your socks and put on some crocks! It's going to be a hot one.",
    "Might want to stay inside, or go to the pool. It will be a bit hot.",
    "Soak up that air conditioning! It's hot out.",
    "Make sure to stay hydrated in this hot weather!"
)

COLD_SAYINGS = (
    "It might be a hat and glove kind of day.",
    "Try to keep warm!",
    "The weather outside is frightful, but the inside is pretty nice.",
    "Break out the handwarmers! It may be hard to type."
)


class Weather:
    def __init__(self, api_key, city_id=None, zip=None, latlon=None, name=None):
        if not city_id or zip or latlon or name:
            raise Exception("Must specify one of city id, zip code, latlon, or name.")
        if city_id:
            loc = "id=" + str(city_id)
        elif zip:
            loc = "zip=" + str(zip)
        elif latlon:
            loc = "lat={0[0]}&lon={0[1]}".format(latlon)
        elif name:
            loc = "q=" + name
        self.uri = '?{}&APPID={}&units=imperial'.format(loc, api_key)

    def get(self, mode='weather'):
        r = requests.get(BASE_URL + mode + self.uri)
        if not r.status_code == 200 or not 'json' in r.headers['content-type']:
            raise Exception("Invalid response from OpenWeatherMap")
        return Forecast(r.json())


class Forecast:
    def __init__(self, data):
        if data.get('list'):
            data = data['list'][1]
        self.temp = data['main']['temp']
        self.description = data['weather'][0]['description']
        self.wind = data['wind']['speed']

    def windy(self):
        return self.wind > 20

    def rainy(self):
        return 'rain' in self.description.lower()


def get_quote():
    r = requests.get('https://quotes.rest/qod', headers={'Accept': 'application/json'})
    if r.status_code == 200:
        return r.json()['contents']['quotes'][0]['quote']


def format_weather(speech):
    weather = speech.weather.get()
    forecast = speech.weather.get('forecast')
    dt = datetime.datetime.now()
    extra = []
    if weather.windy() or forecast.windy():
        extra.append(random.choice(WINDY_SAYINGS))
    if weather.rainy() or forecast.rainy():
        extra.append("Don't forget to bring an umbrella, " + random.choice(RAINY_SAYINGS))
    if weather.temp > 90 or forecast.temp > 90:
        extra.append(random.choice(HOT_SAYINGS))
    if weather.temp < 28 or forecast.temp < 28:
        extra.append(random.choice(COLD_SAYINGS))
    extra.append(get_quote())
    return message.format(part_of_day(dt), speech.name,
                          calendar.day_name[dt.weekday()],
                          calendar.month_name[dt.month],
                          dt.day, round(weather.temp),
                          weather.description,
                          round(forecast.temp),
                          forecast.description,
                          ' '.join(extra))


@app.route('/api/motd', methods=['GET', 'POST'])
@api_auth_required
def motd(**kwargs):
    try:
        speech = get_device(request.values.get('device'))
    except StopIteration:
        abort(404)
    if not speech.driver.klass == Speech:
        raise NotImplementedError
    return format_weather(speech.dev)
