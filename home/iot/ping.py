import socket
from ast import literal_eval

from home.web.utils import send_to_subscribers


class Ping:
    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port

    def ping(self, host=None, port=None):
        host = host or self.host
        port = port or self.port
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((host, port))
            s.shutdown(2)
            s.close()
            return True
        except Exception:
            return False

    def ping_all(self, hosts):
        results = {}
        try:
            with open('.ping.last') as f:
                last_results = literal_eval(f.read())
        except FileNotFoundError:
            last_results = {}
        for target in hosts:
            result = self.ping(target['host'], target['port'])
            if not result and last_results.get(target['host'], True):
                send_to_subscribers("Lost connectivity to " + target['host'])
            elif result and not last_results.get(target['host'], True):
                send_to_subscribers("Restored connectivity to " + target['host'])
            results[target['host']] = result
        with open('.ping.last', 'w') as f:
            f.write(str(results))
        return results
