"""
Telemetry and Health-Monitoring module for SDN Load Balancer.
Handles port-statistic deltas and active probe checks.
"""

import time
import socket
from ryu.lib import hub

class SwitchTelemetry:
    def __init__(self, server_ports):
        self.port_stats = {
            port: {'bytes': 0, 'time': time.time(), 'rate_bps': 0.0}
            for port in server_ports
        }

    def update_port_stats(self, port_no, tx_bytes):
        if port_no in self.port_stats:
            now = time.time()
            prev = self.port_stats[port_no]
            dt = now - prev['time']
            db = tx_bytes - prev['bytes'] if tx_bytes >= prev['bytes'] else 0
            rate = (db / dt) if dt > 0 else 0.0
            self.port_stats[port_no] = {'bytes': tx_bytes, 'time': now, 'rate_bps': rate}

    def get_port_rate(self, port_no):
        return self.port_stats.get(port_no, {}).get('rate_bps', 0.0)

def probe_tcp_service(ip, port=80, timeout=0.4):
    """Performs a non-blocking TCP socket connect probe."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((ip, port))
        sock.close()
        return True
    except (socket.timeout, socket.error):
        return False
