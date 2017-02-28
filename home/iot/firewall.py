from flask import abort
from flask import request

from home.core.models import get_device
from home.iot.wrappers import SSH
from home.web.utils import api_login_required
from home.web.web import app

FIREWALL_TYPES = {
    'iptables': '/sbin/iptables',
    # 'nftables': '/usr/sbin/nft',
}


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

    def delete(self, table='filter', chain='INPUT', rulenum=''):
        if self.firewall == 'iptables':
            return self.send('{} -t {} -D {} {}'.format(
                self.bin, table, chain, rulenum)
            )


@app.route('/api/firewall/unblock', methods=['GET', 'POST'])
@api_login_required
def unblock_this(*args, **kwargs):
    # Todo: expire automatically
    try:
        device = get_device(request.values.get('device'))
    except StopIteration:
        abort(404)
    # Eventually, inheritance on "Firewall" class
    if not isinstance(device.driver.klass, SSHFirewall.__class__):
        raise NotImplementedError
    device.dev.unblock(saddr=request.remote_addr,
                       proto=request.values.get('proto'),
                       dport=request.values.get('dport'))
    return '', 204
