import datetime
import subprocess
from typing import List

import paramiko
import redis
import requests
from flask_socketio import emit
from time import sleep
from wakeonlan import send_magic_packet

from home.core.tasks import run
from home.core.utils import to_float
from home.web.utils import ws_login_required
from home.web.web import socketio

storage = redis.StrictRedis(decode_responses=True)

# Virsh will be queried at most once per this value
SECONDS_BETWEEN_VIRSH_QUERY: float = 1.0
# Max time to wait for all VMs to suspend before suspending the host
MAX_VIRSH_SUSPEND: int = 600


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
                'class': 'btn-danger'
            },
            {
                'text': 'Reboot',
                'method': 'restart',
                'class': 'btn-danger'
            },
        )
    }

    def __init__(self, mac: str = None, host: str = None, port: int = 22, manual_interface: str = None,
                 keyfile: str = "~/.ssh/id_rsa", username: str = "root",
                 password: str = None, os: str = "linux", wakeonlan: str = "native",
                 virt: str = None, vm_port: int = 8888, virsh_seconds: float = SECONDS_BETWEEN_VIRSH_QUERY):
        self.password = password
        self.username = username
        self.keyfile = keyfile
        self.mac = mac
        self.host = host
        self.port = port
        self.interface = manual_interface
        self.os = os
        self.wakeonlan = wakeonlan
        self.vms = []
        self.virt = virt
        self.vm_port = vm_port
        self.virsh_seconds = virsh_seconds

    def on(self):
        self.wake()

    def off(self):
        self.power('off')

    def restart(self):
        self.power('restart')

    def reboot_to(self, boot_option: int):
        if 'linux' not in self.os:
            raise NotImplementedError
        if boot_option >= 0:
            self.run_command('sudo grub-reboot ' + boot_option)
            self.run_command('sudo grub2-reboot ' + boot_option)
            self.restart()

    def wake(self):
        if self.wakeonlan in ('etherwake', 'ether-wake'):
            iface = []
            if self.interface:
                iface = ['-i ' + self.interface]
            for i in range(5):
                subprocess.run(['sudo', '/usr/sbin/ether-wake', *iface, self.mac])
                sleep(0.5)
        elif self.wakeonlan == 'wakeonlan':
            for i in range(5):
                subprocess.run(['sudo', '/usr/bin/wakeonlan', self.mac])
                sleep(0.5)
        elif self.wakeonlan == 'native':
            for i in range(5):
                send_magic_packet(self.mac, ip_address=self.host)
                sleep(0.5)
        else:
            raise NotImplementedError("No valid wake-on-LAN method chosen")

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
        elif state in ['restart', 'reboot']:
            self.run_command('sudo reboot')
        else:
            raise NotImplementedError

    def run_command(self, command: str, user: str = "", password: str = "", keyfile: str = "",
                    capture_output: bool = False) -> List[str]:
        username = user or self.username
        password = password or self.password
        keyfile = keyfile or self.keyfile
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host,
                    self.port,
                    username,
                    password,
                    key_filename=keyfile)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = []
        if capture_output:
            for s in (stdin, stdout, stderr):
                try:
                    output.append(s.readlines())
                except OSError:
                    output.append("")
        ssh.close()
        return output

    def _storage_key(self):
        return f"{self.host}:{self.username}:virsh"

    def get_powered_on_vms(self):
        self.enum_virsh(blocking=True)
        for vm, status in self.vms:
            if not status == "powered off":
                yield vm

    def save_vms_sleep(self):
        for vm in self.get_powered_on_vms():
            run(self.vm_power, thread=True, vm=vm, action='save')
        wait_start = datetime.datetime.now()
        while (datetime.datetime.now() - wait_start).total_seconds() < MAX_VIRSH_SUSPEND:
            if not len(list(self.get_powered_on_vms())):
                self.sleep()
                break
            sleep(15)
        # maybe log failure

    def _enum_virsh(self):
        last_check = datetime.datetime.fromtimestamp(to_float(storage.get(self._storage_key() + ":last")))
        if not (datetime.datetime.now() - last_check).seconds >= self.virsh_seconds:
            return
        storage.set(self._storage_key() + ":last", datetime.datetime.now().timestamp())
        o = None
        try:
            if self.virt == 'http':
                o = requests.get("http://{}:{}/list".format(self.host, self.vm_port)).text.split('\n')
            else:
                o = self.run_command('sudo virsh list --all', capture_output=True)[1]
        except:
            pass
        finally:
            storage.delete(self._storage_key())
        if not o:
            return
        for line in o[2:-1]:
            if line:
                storage.rpush(self._storage_key(), line)

    def enum_virsh(self, blocking: bool = False):
        if blocking:
            self._enum_virsh()
        else:
            run(self._enum_virsh, thread=True)
        vms = set()
        for line in storage.lrange(self._storage_key(), 0, -1):
            if line:
                line = line.split()
                status = ' '.join(line[2:])
                vms.add((line[1], status))
        self.vms = sorted(list(vms), key=lambda x: x[1])

    def vm_power(self, vm: str, action: str = 'start'):
        if action in ('start', 'shutdown', 'reboot', 'suspend', 'resume', 'save', 'restore'):
            if self.virt == 'http':
                requests.post("http://{}:{}/vm/{}/power/{}".format(self.host, self.vm_port, vm, action))
            else:
                # Won't work with 'save'
                self.run_command('sudo virsh {} {}'.format(action, vm))


@socketio.on('enum virsh')
@ws_login_required(check_device=True)
def get_vms(message, device):
    if device.dev.virt:
        device.dev.enum_virsh()
        emit('vms', {"device": message['device'], "vms": device.dev.vms})


@socketio.on('vm ctrl')
@ws_login_required(check_device=True)
def vm_ctrl(message, device):
    run(device.dev.vm_power, thread=True, vm=message['vm'], action=message['action'])
    emit('message',
         {'class': 'alert-success',
          'content': "Requested '{}' on '{}'".format(message['action'],
                                                            message['vm'])
          })
