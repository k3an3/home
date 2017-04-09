import calendar
import datetime

import requests
from flask import request, abort

from home.core.models import get_device
from home.iot.speech import Speech, message
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
        return r.json()


@app.route('/api/motd', methods=['GET', 'POST'])
@api_auth_required
def motd(**kwargs):
    try:
        speech = get_device(request.values.get('device'))
    except StopIteration:
        print('hi')
        abort(404)
    if not speech.driver.klass == Speech:
        raise NotImplementedError
    speech = speech.dev
    weather = speech.weather.get()
    forecast = speech.weather.get('forecast')
    dt = datetime.datetime.now()
    return message.format(speech.name, calendar.day_name[dt.weekday()], calendar.month_name[dt.month], dt.day,
                          round(weather['main']['temp']),
                          weather['weather'][0]['description'],
                          round(forecast['list'][1]['main']['temp']),
                          forecast['list'][1]['weather'][0]['description'])
