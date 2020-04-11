import json
import socket
from abc import ABC, abstractmethod
from ipaddress import ip_address
from typing import Dict

from flask import request

from home.web.utils import api_auth_required
from home.web.web import app

FIREWALL_TYPES = {
    'iptables': '/sbin/iptables',
    # 'nftables': '/usr/sbin/nft',
}


class Firewall(ABC):
    """
    widget = {
        'form': {
            'input': (
            {
                'text': 'On',
                'function': 'on',
            },
            ),
            {
                'text': 'Off',
                'function': 'off',
                'class': 'btn-danger'
            },
        }
    }
    """

    @abstractmethod
    def unblock(self, saddr, proto, dport, duration=None):
        pass

    @abstractmethod
    def reset(self):
        pass


class RemoteFirewall(Firewall):
    def __init__(self, host: str, port: int, secret: str = "", users: Dict = {}):
        self.host = host
        self.port = port
        self.secret = secret
        self.users = users

    def _communicate(self, data: Dict):
        s = socket.create_connection((self.host, self.port), timeout=10)
        data['secret'] = self.secret
        s.send(json.dumps(data).encode())
        s.close()

    def reset(self):
        pass

    def unblock(self, saddr: str, **kwargs) -> str:
        if (table := kwargs.get('table')) and (
                table.split()[0] not in ('ip', 'inet') or table.split()[1] not in ('filter', 'nat')):
            return "Invalid table"
        if (chain := kwargs.get('chain')) and chain not in ('input', 'forward', 'output', 'prerouting', 'postrouting'):
            return "Invalid chain"
        if (proto := kwargs.get('proto')) and proto not in ('icmp', 'tcp', 'udp'):
            try:
                int(proto)
            except ValueError:
                try:
                    int(proto, 16)
                except ValueError:
                    return "Invalid proto"
        try:
            ip_address(saddr)
        except ValueError:
            return "Invalid saddr"
        if dport := kwargs.get('dport'):
            try:
                if not 0 < int(dport) < 65536:
                    return "Invalid dport"
            except ValueError:
                return "Invalid dport"
        if (timeout := kwargs.get('timeout')) and timeout < 0:
            return "Invalid timeout"
        data = {'table': table, 'chain': chain, 'proto': proto,
                'saddr': saddr, 'dport': dport, 'timeout': timeout}
        if user := kwargs.get('user'):
            if user in self.users:
                data.update(self.users[user])
        self._communicate(data)


"""
class SSHFirewall(SSH):

    def __init__(self, firewall="iptables", path=FIREWALL_TYPES['iptables'], *args, **kwargs):
        super().__init__(*args, **kwargs)
        if firewall not in FIREWALL_TYPES:
            raise NotImplementedError
        self.firewall = firewall
        self.bin = path

    def command(self, rule):
        return self.send('{} {}'.format(FIREWALL_TYPES[self.firewall], rule))

    def unblock(self, saddr, proto, dport):
        if self.firewall == 'iptables':
            return self.send('{} -I INPUT -s {} -p {} --dport {} -j ACCEPT'.format(
                self.bin, saddr, proto, dport
            ))
        elif self.firewall == 'nftables':
            table = 'inet filter' # todo
            return self.send(f'{self.bin} insert rule {table} {proto} {dport} counter accept')

    def delete(self, table='filter', chain='INPUT', rulenum='', format=''):
        if self.firewall == 'iptables':
            return self.send('{} -t {} -D {} {}'.format(
                self.bin, table, chain, rulenum or format)
            )
"""


@app.route('/api/firewall/unblock', methods=['POST'])
@api_auth_required(check_device=True)
def unblock_this(client, device):
    if not isinstance(Firewall, device.dev):
        raise NotImplementedError
    remote_addr = request.environ['HTTP_X_REAL_IP'] or request.remote_addr
    device.dev.unblock(table=request.form.get('table'), chain=request.form.get('chain'),
                       saddr=remote_addr,
                       proto=request.values.get('proto'),
                       dport=request.values.get('dport'),
                       timeout=request.values.get('timeout', None),
                       user=client.name,
                       )
    return '', 204
