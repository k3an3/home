import calendar
import datetime
import random

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

INSPIRATION = (
    "Whatever you are, be a good one.",
    "If you dream it, you can do it.",
    "Every moment is a beginning",
    "Never, never, never give up.",
    "Don’t wait. The time will never be just right.",
    "If not us, who? If not now, when?",
    "Everything you can imagine is real.",
    "I can, therefore I am.",
    "Follow Your Bliss",
    "Remember no one can make you feel inferior without your consent.",
    "Turn your wounds into wisdom.",
    "Wherever you go, go with all your heart.",
    "Do what you can, with what you have, where you are.",
    "Hope is a waking dream.",
    "Action is the foundational key to all success.",
    "Do one thing every day that scares you.",
    "You must do the thing you think you cannot do.",
    "Life is trying things to see if they work.",
    "Don’t regret the past, just learn from it.",
    "Believe you can and you’re halfway there.",
    "Live what you love.",
    "The power of imagination makes us infinite.",
    "May you live every day of your life.",
    "Eighty percent of success is showing up.",
    "To be the best, you must be able to handle the worst.",
    "A jug fills drop by drop.",
    "The obstacle is the path.",
    "The best revenge is massive success.",
    "You get what you settle for",
    "The best way out is always through.",
    "If you have never failed you have never lived.",
    "Hope is the heartbeat of the soul.",
    "Ever tried. Ever failed. No matter. Try Again. Fail again. Fail better.",
    "All you need is love.",
    "It does not matter how slowly you go as long as you do not stop.",
    "It is never too late to be what you might have been.",
    "We become what we think about.",
    "An obstacle is often a stepping stone.",
    "Dream big and dare to fail.",
    "Men are born to succeed, not fail.",
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
    extra.append(random.choice(INSPIRATION))
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
