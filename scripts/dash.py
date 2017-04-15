#!/usr/bin/env python3
"""
dash.py
~~~~~~~

Receiver for Amazon Dash button push events.

Supports two modes: "arp" and "dns". In both cases, set up the Amazon dash button like normal, following the directions,
until it asks you to pick a product. At this point, you can back out of the app. I'd recommend setting a firewall rule
blocking outbound traffic from the buttons, otherwise you will receive an annoying notification from the app each time 
the button is pressed, asking you to finish setting it up.

"arp" is roughly based on methods linked from 
http://www.dashbuttondudes.com/blog/2015/12/11/26-amazon-dash-button-hacks to capture the button events. When the 
button connects, it will first ARP for the gateway. We can use this ARP to capture the button press. This requires 
that the button and this receiver be on the same layer 2 subnet. 

"dns" is used in the case that the button and this receiver are on different layer 2 subnets. This may be the case if
an isolated network is used for IoT devices such as the dash button. Firewall rules need to be added to the network's 
router such that traffic from the buttons is intercepted. It is also helpful to assign static ip addresses to the buttons. 

For example, to redirect traffic from a button at 192.168.1.127 to the receiver at 172.24.0.25, add the following:
```
iptables -t nat -A PREROUTING -s 192.168.1.127 -j DNAT --to-destination 172.24.0.25
```

Additionally, since this need not be run at root and is binding to a port other than 53, add the following rule to this 
machine in order to allow the traffic to reach us:
```
iptables -t nat -A PREROUTING -p udp --dport 53 -j REDIRECT --to-port 5354
```
However, this method is currently unsupported because we'd need to only count the first of many DNS requests.
"""

import sys

import requests

API_TOKEN = 'API_TOKEN'
CONTROLLER_URL = 'https://105ww.xyz/api/command'
TARGET_HWADDRS = {'68:54:FD:26:B3:58': 'energizer', '40:B4:CD:7F:8B:5B': 'glad'}
TARGET_IPADDRS = {'192.168.1.127': 'energizer', '192.168.1.128': 'glad'}


def report(button):
    requests.post(CONTROLLER_URL, data={'key': API_TOKEN, 'action': 'dash_' + button})


def capture_arp(pkt):
    if pkt[ARP].op == 1 and pkt[ARP].psrc == '0.0.0.0':
        target = TARGET_HWADDRS.get(pkt[ARP].hwsrc)
        if target:
            print("Received ARP from", target)
            report(target)


def listen_dns():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('127.0.0.1', 5354))
    while True:
        data, addr = s.recvfrom(1024)
        if addr[0] in TARGET_IPADDRS:
            print("Received valid packet from", TARGET_IPADDRS[addr[0]])
            report(TARGET_IPADDRS[addr[0]])
        else:
            print("Received unexpected packet from", addr[0])


if len(sys.argv) == 2:
    if sys.argv[1] == 'arp':
        from scapy.sendrecv import sniff
        from scapy.layers.l2 import ARP

        sniff(prn=capture_arp, filter="arp", store=0, count=10)
    elif sys.argv[1] == 'dns':
        listen_dns()
print("Error: Must specify one of 'arp' or 'dns'")
