import re

import requests
from requests.auth import HTTPBasicAuth

# https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/components/device_tracker/ddwrt.py
_DDWRT_DATA_REGEX = re.compile(r'\{(\w+)::([^\}]*)\}')
_MAC_REGEX = re.compile(r'(([0-9A-Fa-f]{1,2}\:){5}[0-9A-Fa-f]{1,2})')


def _parse_ddwrt_response(data_str):
    """Parse the DD-WRT data format."""
    return {
        key: val for key, val in _DDWRT_DATA_REGEX
        .findall(data_str)
    }
# End copy


class DDwrt:
    def __init__(self, host: str, proto: str = 'http', port: int = 80, username: str = None, password: str = None):
        self.host = host
        self.proto = proto
        self.port = port
        self.auth = HTTPBasicAuth(username, password)

    def get(self, path):
        r = requests.get("{}://{}:{}/{}".format(
            self.proto, self.host, self.port, path), auth=self.auth, verify=False)
        if not r.status_code == 200:
            raise ConnectionError("Authentication Failed")
        return _parse_ddwrt_response(r.text)

    def get_active_clients(self):
        return self.get('Status_Lan.live.asp').get('arp_table')
