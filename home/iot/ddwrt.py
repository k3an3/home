import json
import re
from typing import List, Dict

import requests
from flask_socketio import emit
from requests.auth import HTTPBasicAuth

from home.core.models import get_device
from home.web.utils import ws_login_required
from home.web.web import socketio, app

_ACTIVE_CLIENTS_REGEX = re.compile(
    r"'([\w\d*-]+)','((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4]["
    r"0-9]|25[0-5]))','(([0-9A-Fa-f]{1,2}\:){5}[0-9A-Fa-f]{1,2})','\d+',?")
# https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/components/device_tracker/ddwrt.py
_DDWRT_DATA_REGEX = re.compile(r'\{(\w+)::([^\}]*)\}')
_MAC_REGEX = re.compile(r'(([0-9A-Fa-f]{1,2}\:){5}[0-9A-Fa-f]{1,2})')


def _parse_ddwrt_response(data_str):
    """Parse the DD-WRT data format."""
    return {
        key: val for key, val in _DDWRT_DATA_REGEX
        .findall(data_str)
    }


def _parse_clients(data_str):
    clients = {}
    for client in _ACTIVE_CLIENTS_REGEX.findall(data_str):
        clients[client[5]] = {'hostname': client[0] if not client[0] == '*' else None,
                              'ip_addr': client[1],
                              }
    return clients


# End copy
def get_social_avatar(username: str, network: str = "facebook", size: str = ""):
    return "https://avatars.io/{1}/{0}/{2}".format(username, network, size)


class DDwrt:
    def __init__(self, host: str, proto: str = 'http', port: int = None, username: str = None, password: str = None,
                 users: List[Dict] = []):
        self.host = host
        self.proto = proto
        self.port = port if port else 443 if proto == 'https' else 80
        self.auth = HTTPBasicAuth(username, password)
        for user in users:
            if user.get('username'):
                user['avatar'] = get_social_avatar(username=user['username'], network="facebook", size="medium")
        self.users = users

    def get(self, path):
        r = requests.get("{}://{}:{}/{}".format(
            self.proto, self.host, self.port, path), auth=self.auth, verify=False)
        if not r.status_code == 200:
            raise ConnectionError("Authentication Failed")
        return _parse_ddwrt_response(r.text)

    def get_active_clients(self):
        return _parse_clients(self.get('Status_Lan.live.asp').get('arp_table'))

    def clients_to_users(self):
        clients = self.get_active_clients()
        users = []
        for user in self.users:
            client = clients.get(user['mac_addr'])
            if client:
                client.update(user)
                users.append(client)
        return users


@socketio.on('get presence')
@ws_login_required
def get_presence():
    dd = get_device('router').dev
    users = dd.clients_to_users()
    emit('presence data', users)


@app.route('/api/presence')
def get_presence_api():
    dd = get_device('router').dev
    users = dd.clients_to_users()
    return json.dumps(users)
