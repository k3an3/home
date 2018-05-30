import re
import subprocess

import paramiko
from wakeonlan.wol import send_magic_packet


def escape(command):
    return re.sub(r'[&|]', '', command)


class Computer:
    widget = {
        'buttons': (
            {
                'text': 'Wake',
                'method': 'wake',
                'class': 'btn-success'
            },
            {
                'text': 'Sleep',
                'method': 'sleep',
                'class': 'btn-warning'
            },
            {
                'text': 'Shut Down',
                'method': 'power',
                'config': {'state': 'off'},
                'class': 'btn-warning'
            },
        )
    }

    def __init__(self, mac, host=None, port=None, manual_interface=None, keyfile="~/.ssh/id_rsa", username="root",
                 password=None, os: str = "linux"):
        self.password = password
        self.username = username
        self.keyfile = keyfile
        self.mac = mac
        self.host = host
        self.port = port
        self.interface = manual_interface
        self.os = os

    def wake(self):
        if self.interface:
            subprocess.run(['sudo', '/usr/sbin/ether-wake', '-i', self.interface, self.mac])
        else:
            send_magic_packet(self.mac, ip_address=self.host, port=self.port)

    def sleep(self):
        if self.os == "linux":
            self.run_command('sudo systemctl suspend')
        elif self.os == "linux-old":
            self.run_command('pm-suspend')
        else:
            raise NotImplementedError

    def power(self, state: str = 'on'):
        if state == 'on':
            self.wake()
        elif state == 'off':
            self.run_command('sudo poweroff')
        elif state in ['sleep', 'suspend']:
            self.sleep()

    def run_command(self, command: str) -> str:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host,
                    self.port,
                    self.username,
                    self.password,
                    key_filename=self.keyfile)
        r = ssh.exec_command(escape(command))[2].readlines()
        ssh.close()
        return r
