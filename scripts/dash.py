from scapy.all import *
import requests

API_TOKEN = 'API_TOKEN'
CONTROLLER_URL = 'https://105ww.xyz/api/command'
TARGET_HWADDRS = {'68:54:FD:26:B3:58': 'energizer', '40:B4:CD:7F:8B:5B': 'glad'}


def report(button):
    requests.post(CONTROLLER_URL, data={'key': API_TOKEN, 'action': 'dash_' + button})


def capture_arp(pkt):
    if pkt[ARP].op == 1 and pkt[ARP].psrc == '0.0.0.0':
            if pkt[ARP].hwsrc in TARGET_HWADDRS:
                report(TARGET_HWADDRS[pkt[ARP].hwsrc])


sniff(prn=capture_arp, filter="arp", store=0, count=10)
