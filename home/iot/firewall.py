from home.iot.wrappers import SSH

FIREWALL_TYPES = {
    'iptables': '/sbin/iptables',
    # 'nftables': '/usr/sbin/nft',
}


class SSHFirewall(SSH):
    def __init__(self, firewall="iptables", *args, **kwargs):
        super().__init__(*args, **kwargs)
        if firewall not in FIREWALL_TYPES:
            raise NotImplementedError
        self.firewall = firewall

    def command(self, rule):
        return self.send('{} {}'.format(FIREWALL_TYPES[self.firewall], rule))

    def add_incoming(self, saddr, proto, dport):
        if self.firewall == 'iptables':
            return self.send('{} -I INPUT -s{} -p{} --dport={} -j ACCEPT'.format(
                self.firewall, saddr, proto, dport
            ))

    def delete(self, table='filter', chain='INPUT', rulenum=''):
        if self.firewall == 'iptables':
            return self.send('{} -t{} -A{} -D{}'.format(
                self.firewall, table, chain, rulenum)
            )
