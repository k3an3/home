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
    "Drop your socks and put on your crocs! It's going to be a wet one.",
    "You know what they say about April showers. That would be awkward if it wasn't April..."
)

WINDY_SAYINGS = (
    "Hold on to your hat! It's going to be a breezy one.",
    "Batten down the hatches! It may get windy.",
    "Watch out for falling trees on this windy day!",
    "The wind might just blow you over today.",
)

HOT_SAYINGS = (
    "Might want to stay inside, or go to the pool. It will be a bit hot.",
    "Soak up that air conditioning! It's hot out.",
    "Make sure to stay hydrated in this hot weather!",
    "Spend some quality time inside today, it'll be hot out there.",
    "Spend some time in the freshest possible air! Good old A C.",
    "Head for the beach. Or don't. Up to you.",
    "Put away your cloudblock and make sure to use plenty of sunblock!"
)

COLD_SAYINGS = (
    "It might be a hat and glove kind of day.",
    "Try to keep warm!",
    "The weather outside is frightful, but the inside is pretty darn nice.",
    "Break out the handwarmers! It may be hard to type.",
    "Crank up the heater and get toasty!",
    "Better put another log on the fire, it is cold out!",
    "Summer called, and wanted to make you jealous of the weather."
)

SNOWY_SAYINGS = (
    "Put on your snowshoes, you'll need them today.",
    "Gone away is the bluebird, here to stay is the new bird. a k a, it might be a winter wonderland out there.",
    "Don't go to Dairy Queen today, eat some snow instead!",
    "Might just be a good day for a snowball fight! What about the possibility of an aerial attack?",
    "Just because it's snowing doesn't mean you get the day off.",
    "Hope the roads are clean; driving could get interesting."
)

STORMY_SAYINGS = (
    "Stay away from doors and windows!",
    "You may want to seek shelter indoors today.",
    "Don't get struck by lightning!",
    "Thunder and lightning from above!",
    "Hope the dog isn't scared of thunder.",
    "Unplug all of your applicances and do not shower unless you dare.",
    "Do you think we'll set a record for hail size today?",
)


class Weather:
    def __init__(self, api_key):
        self.api_key = api_key

    def get(self, city_id=None, zipcode=None, latlon=None, name=None, mode='weather'):
        if city_id:
            loc = "id=" + str(city_id)
        elif zipcode:
            loc = "zip=" + str(zipcode)
        elif latlon:
            loc = "lat={0[0]}&lon={0[1]}".format(latlon.split(','))
        elif name:
            loc = "q=" + name
        uri = '?{}&APPID={}&units=imperial'.format(loc, self.api_key)
        r = requests.get(BASE_URL + mode + uri)
        if not r.status_code == 200 or not 'json' in r.headers['content-type']:
            raise Exception("Invalid response from OpenWeatherMap")
        return Forecast(r.json())

    @staticmethod
    def render_widget(lat, lon):
        return '<iframe src="https://weatherfor.us/widget?" scrolling="no" frameborder="0" allowtransparency="true" ' \
               'style="background: transparent; width: 720px; height: 250px; overflow: hidden;"></iframe> <img ' \
               'src="https://radblast.wunderground.com/cgi-bin/radar/WUNIDS_map?station=DMX&brand=wui&num=6&delay=15' \
               '&type=N0R&frame=0&scale=1.000&noclutter=0&showstorms=0&mapx=400&mapy=240&centerx=400&centery=240' \
               '&transx=0&transy=0&showlabels=1&severe=0&rainsnow=0&lightning=0&smooth=0&rand=25060044&lat={}' \
               '&lon={}">'.format(lat, lon)


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
    data = dict(request.values)
    try:
        speech = get_device(data.pop('device'))
    except StopIteration:
        abort(404)
    if not speech.driver.klass == Speech:
        raise NotImplementedError
    if not client.has_permission(speech.group):
        abort(403)
    speech = speech.dev
    weather = speech.weather.get(**data)
    forecast = speech.weather.get(**data, mode='forecast')
    return format_weather(weather, forecast, speech)
