import calendar
import datetime

import requests
from flask import request, abort

from home.core.models import get_device
from home.iot.speech import Speech, message, part_of_day
from home.web.utils import api_auth_required
from home.web.web import app

BASE_URL = "http://api.openweathermap.org/data/2.5/"


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
        extra.append("Hold on to your hat! It's going to be a breezy one.")
    if weather.rainy() or forecast.rainy():
        extra.append("Don't forget to bring an umbrella!")
    if weather.temp > 90 or forecast.temp > 90:
        extra.append("It's gonna get toasty!")
    if weather.temp < 28 or forecast.temp < 28:
        extra.append("It's a hat and glove kind of day.")
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
