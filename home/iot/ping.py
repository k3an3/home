import socket

from home.web.utils import send_to_subscribers


class Ping:
    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.state = {}

    def ping(self, host=None, port=None):
        host = host or self.host
        port = port or self.port
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((host, port))
            s.shutdown(2)
            s.close()
            self.state[host] = True
        except Exception as e:
            if self.state.get('host'):
                send_to_subscribers("Failed to ping " + host)
            self.state[host] = False
            return e

    def ping_all(self, hosts):
        results = []
        for target in hosts:
            results.append(self.ping(target['host'], target['port']))
        return results
