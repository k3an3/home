import datetime
import requests
from flask_socketio import emit

from home.core.models import get_device
from home.web.utils import ws_login_required
from home.web.web import socketio

NEXTBUS_URL = 'http://webservices.nextbus.com/service/publicJSONFeed?a=cyride&command=predictions&stopId={}'


class NextBus:
    def __init__(self, stop_id: int):
        self.stop_id = stop_id
        self.data_time = datetime.datetime.fromtimestamp(0)
        self.data = None

    def get_predictions(self):
        r = requests.get(NEXTBUS_URL.format(self.stop_id))
        upcoming = []
        if r.status_code == 200:
            predictions = r.json()['predictions']
            for p in predictions:
                if p.get('direction'):
                    times = []
                    for prediction in p['direction']['prediction']:
                        try:
                            times.append(int(prediction['epochTime']))
                        except TypeError:
                            pass
                    upcoming.append((p['routeTitle'], times))
        self.data_time = datetime.datetime.now()
        self.data = upcoming

    def render_widget(self):
        return '<img src="https://www.stugov.iastate.edu/assets/images/logo.png" height="100"/><h1>Next Bus</h1><div' \
               ' id="nextbusdata"></div>'


@socketio.on('next bus')
@ws_login_required
def next_bus():
    nb = get_device('nextbus').dev
    if (datetime.datetime.now() - nb.data_time).total_seconds() / 60 >= 5:
        nb.get_predictions()
    emit('next bus data', nb.data)
