from flask import abort
from flask import request

from home.core.async import run
from home.core.models import get_device
from home.iot.wrappers import SSH
from home.web.utils import api_auth_required
from home.web.web import app

FIREWALL_TYPES = {
    'iptables': '/sbin/iptables',
    # 'nftables': '/usr/sbin/nft',
}


class SSHFirewall(SSH):
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

    def delete(self, table='filter', chain='INPUT', rulenum='', format=''):
        if self.firewall == 'iptables':
            return self.send('{} -t {} -D {} {}'.format(
                self.bin, table, chain, rulenum or format)
            )


@app.route('/api/firewall/unblock', methods=['GET', 'POST'])
@api_auth_required
def unblock_this(client):
    try:
        device = get_device(request.values.get('device'))
    except StopIteration:
        abort(404)
    # Eventually, inheritance on "Firewall" class
    if not device.driver.klass == SSHFirewall:
        raise NotImplementedError
    if not client.has_permission(device.group):
        abort(403)
    remote_addr = request.environ['HTTP_X_REAL_IP'] or request.remote_addr
    device.dev.unblock(saddr=remote_addr,
                       proto=request.values.get('proto'),
                       dport=request.values.get('dport'))
    device.dev.unblock(saddr=remote_addr,
                       proto=request.values.get('proto'),
                       dport=request.values.get('dport') + ' -m state --state RELATED,ESTABLISHED')
    queue_reblock(device, remote_addr, request)
    return '', 204


def queue_reblock(device, remote_addr, request):
    run(device.dev.delete, delay=300, **{
        'format': '-s {} -p {} --dport {} -j ACCEPT'.format(
            remote_addr, request.values.get('proto'),
            request.values.get('dport')
        )
    })
    run(device.dev.delete, delay=86400, **{
        'format': '-s {} -p {} --dport {} -m state --state RELATED,ESTABLISHED -j ACCEPT'.format(
            remote_addr, request.values.get('proto'),
            request.values.get('dport')
        )
    })
