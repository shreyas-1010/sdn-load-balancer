# System Architecture

## OpenFlow State & Header Mutation Pipeline

```
Client (h1)                Open vSwitch (s1)             Ryu Controller
│                             │                             │
├─────── ARP Request ────────>│                             │
│   "Who is 10.0.0.100?"      ├────── Packet-In ───────────>│
│                             │                             ├── Synthesis: ARP Reply
│<────── ARP Reply ───────────┼────── Packet-Out ───────────┤   (VIP -> 00:00:00:00:00:FE)
│                             │                             │
├─────── TCP SYN (VIP) ──────>│                             │
│                             ├────── Packet-In ───────────>│
│                             │                             ├── Select Least-Loaded Port
│                             │<───── FlowMod (Fwd + Rev) ──┤   via SwitchTelemetry
│                             ├── [Install Flow: Priority 10]
│                             │
│                             ├── [Hardware Forwarding Engine]
│                             │   • Inbound:  set_dst(10.0.0.x), set_eth_dst(server_mac)
│                             │   • Outbound: set_src(10.0.0.100), set_eth_src(virtual_mac)
│                             │
│<═════ Wire-Speed Streaming ═╪═════════════════════════════> (h2, h3, or h4)
```

## Resilience & Flow Lifecycle
1. **Periodic Telemetry Loop:** Ryu sends `OFPPortStatsRequest` every 2 seconds. The delta byte count determines instantaneous link usage.
2. **Dynamic Server Health Checking:** Active TCP handshakes cycle every 3 seconds.
3. **Reactive Flow Eviction:** If a backend server transitions to `OFFLINE`, an `OFPFC_DELETE` command flushes all flow table rules containing that node's IP address.
