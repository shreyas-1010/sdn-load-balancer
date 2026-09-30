#!/usr/bin/env python3
"""
Custom Mininet network topology module with bandwidth limits and HTTP daemons.
Sets up 1 switch, 1 client, and 3 backend servers with constrained links.
"""

import os
import json
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config/topology_config.json')

def run():
    with open(CONFIG_PATH, 'r') as f:
        cfg = json.load(f)

    net = Mininet(controller=RemoteController, switch=OVSSwitch, link=TCLink, autoSetMacs=True)

    info('*** Connecting to Remote Ryu Controller\n')
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633)

    info('*** Adding Switch\n')
    s1 = net.addSwitch('s1', protocols='OpenFlow13')

    info('*** Adding Host Nodes\n')
    h1 = net.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
    servers = []
    for s in cfg['servers']:
        srv = net.addHost(s['id'], ip=f"{s['ip']}/24", mac=s['mac'])
        servers.append(srv)

    info('*** Configuring Bandwidth-Constrained Links\n')
    bw = cfg['link_bandwidth_mbps']
    delay = cfg['link_delay_ms']
    net.addLink(h1, s1, bw=bw, delay=delay)
    for srv in servers:
        net.addLink(srv, s1, bw=bw, delay=delay)

    info('*** Launching Network\n')
    net.start()

    info('*** Starting Python HTTP Micro-servers on Replicas\n')
    for srv in servers:
        srv.cmd('python3 -m http.server 80 &')

    info('*** Mininet cluster online. Drop into interactive CLI.\n')
    CLI(net)

    info('*** Stopping Network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
