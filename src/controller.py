#!/usr/bin/env python3
"""
Least-Loaded Fault-Tolerant OpenFlow 1.3 Load Balancer Controller.
Implements dynamic load balancing with health checks and automatic failover.
"""

import os
import json
import time
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
from ryu.lib.packet import packet, ethernet, ipv4, arp, tcp

from src.monitor import SwitchTelemetry, probe_tcp_service

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config/topology_config.json')

class ResilientSDNController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ResilientSDNController, self).__init__(*args, **kwargs)
        with open(CONFIG_PATH, 'r') as f:
            self.cfg = json.load(f)

        self.virtual_ip = self.cfg['virtual_ip']
        self.virtual_mac = self.cfg['virtual_mac']
        self.servers = [dict(s, alive=True) for s in self.cfg['servers']]
        
        self.telemetry = SwitchTelemetry([s['port'] for s in self.servers])
        self.datapath = None

        # Spawn asynchronous telemetry and health-check loops
        self.stats_thread = hub.spawn(self._stats_monitor_loop)
        self.health_thread = hub.spawn(self._health_check_loop)
        self.logger.info("SDN Resilient Controller Initialized.")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        self.datapath = ev.msg.datapath
        ofproto = self.datapath.ofproto
        parser = self.datapath.ofproto_parser

        # Install table-miss entry: forward unmatched traffic to controller
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFFlowMod(datapath=self.datapath, priority=0, match=match, instructions=inst)
        self.datapath.send_msg(mod)
        self.logger.info("Table-miss flow rule installed on switch s1.")

    def _stats_monitor_loop(self):
        while True:
            if self.datapath:
                parser = self.datapath.ofproto_parser
                req = parser.OFPPortStatsRequest(self.datapath, 0, self.datapath.ofproto.OFPP_ANY)
                self.datapath.send_msg(req)
            hub.sleep(2)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        for stat in ev.msg.body:
            self.telemetry.update_port_stats(stat.port_no, stat.tx_bytes)

    def _health_check_loop(self):
        while True:
            for s in self.servers:
                alive = probe_tcp_service(s['ip'], 80)
                if s['alive'] != alive:
                    s['alive'] = alive
                    status = "ONLINE" if alive else "OFFLINE"
                    self.logger.warning("Backend node %s (%s) transitioned to %s", s['ip'], s['id'], status)
                    if not alive and self.datapath:
                        self._evict_server_flows(s['ip'])
            hub.sleep(3)

    def _evict_server_flows(self, server_ip):
        ofproto = self.datapath.ofproto
        parser = self.datapath.ofproto_parser
        for m in [{'ipv4_dst': server_ip}, {'ipv4_src': server_ip}]:
            match = parser.OFPMatch(eth_type=0x0800, **m)
            mod = parser.OFFlowMod(
                datapath=self.datapath, command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY, match=match
            )
            self.datapath.send_msg(mod)
        self.logger.info("Flushed active OpenFlow flow rules for node: %s", server_ip)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        # Handle ARP for VIP
        if arp_pkt and arp_pkt.dst_ip == self.virtual_ip:
            self._send_arp_reply(datapath, eth.src, arp_pkt.src_ip, in_port)
            return

        # Handle TCP HTTP requests targeting VIP
        if ip_pkt and ip_pkt.dst == self.virtual_ip:
            active_pool = [s for s in self.servers if s['alive']]
            if not active_pool:
                self.logger.error("All backend servers are dead. Packet dropped.")
                return

            # Select backend with the lowest delta transmission rate
            chosen = min(active_pool, key=lambda s: self.telemetry.get_port_rate(s['port']))

            # Forward Path: Client -> Backend Server
            match_fwd = parser.OFPMatch(in_port=in_port, eth_type=0x0800, ip_proto=6, ipv4_dst=self.virtual_ip)
            actions_fwd = [
                parser.OFPActionSetField(ipv4_dst=chosen['ip']),
                parser.OFPActionSetField(eth_dst=chosen['mac']),
                parser.OFPActionOutput(chosen['port'])
            ]
            self._install_flow(datapath, 10, match_fwd, actions_fwd, buffer_id=msg.buffer_id, data=msg.data)

            # Reverse Path: Backend Server -> Client
            match_rev = parser.OFPMatch(in_port=chosen['port'], eth_type=0x0800, ip_proto=6, ipv4_src=chosen['ip'])
            actions_rev = [
                parser.OFPActionSetField(ipv4_src=self.virtual_ip),
                parser.OFPActionSetField(eth_src=self.virtual_mac),
                parser.OFPActionOutput(in_port)
            ]
            self._install_flow(datapath, 10, match_rev, actions_rev)

    def _install_flow(self, datapath, priority, match, actions, buffer_id=None, data=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFFlowMod(
            datapath=datapath, priority=priority, match=match,
            instructions=inst, idle_timeout=5,
            buffer_id=buffer_id if buffer_id else ofproto.OFP_NO_BUFFER
        )
        datapath.send_msg(mod)

    def _send_arp_reply(self, datapath, dst_mac, dst_ip, port):
        parser = datapath.ofproto_parser
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=0x0806, dst=dst_mac, src=self.virtual_mac))
        pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY, src_mac=self.virtual_mac, src_ip=self.virtual_ip,
                                 dst_mac=dst_mac, dst_ip=dst_ip))
        pkt.serialize()
        actions = [parser.OFPActionOutput(port)]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=datapath.ofproto.OFP_NO_BUFFER,
                                  in_port=datapath.ofproto.OFPP_CONTROLLER, actions=actions, data=pkt.data)
        datapath.send_msg(out)
