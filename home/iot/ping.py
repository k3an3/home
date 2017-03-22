import socket

from home.web.utils import send_to_subscribers


class Ping:
    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port

    def ping(self, hosts=None, port=None):
        host = hosts or self.host
        port = port or self.port
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.shutdown(2)
            s.close()
        except Exception as e:
            send_to_subscribers("Failed to ping " + host)
            return e

    def ping_all(self, hosts):
        results = []
        for target in hosts:
            results.append(self.ping(target['host'], target['port']))
        return results
