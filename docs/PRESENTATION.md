# SDN Load Balancing & Response Time Optimization
## Technical Defense & Architecture Walkthrough

---

### Slide 1: Problem Statement & Motivation
- **Hardware Bottlenecks:** Dedicated Layer-7 appliance balancers introduce significant Capex and operational fragility.
- **Bufferbloat & Hotspots:** Static scheduling models fail to adjust to variable TCP streaming payloads, saturating switch egress queues.
- **Solution:** Software-Defined Networking offloads load-balancing decisions to OpenFlow switches for wire-speed header rewriting.

---

### Slide 2: Infrastructure Topology & Flow Translation
- **Components:** 1 Open vSwitch (`s1`), 1 Client (`h1`), 3 HTTP Replicas (`h2-h4`), 1 Ryu Controller.
- **Virtual IP (VIP):** Client targets virtual gateway `10.0.0.100`.
- **Bidirectional Header Mutation:**
  - Forward: `dl_dst` and `nw_dst` rewritten to selected replica.
  - Reverse: `dl_src` and `nw_src` rewritten back to VIP values.

---

### Slide 3: Real-Time Telemetry & Failover
- **Least-Loaded Metric:** Controller polls `OFPPortStatsRequest` every 2s, calculating Δtx_bytes / Δt per port.
- **Failover Logic:** Background micro-thread conducts TCP handshakes.
- **Instant Eviction:** On node termination, controller issues `OFPFC_DELETE` flow mods to prevent dropped packets.

---

### Slide 4: Empirical Findings & Conclusion
- **Throughput:** Improved from **312.4 req/s** to **891.2 req/s** (+185%).
- **Latency:** Mean response time dropped from **128.0 ms** to **44.9 ms** (-65%).
- **Tail Latency:** 99th percentile dropped from **310 ms** to **92 ms**.
- **Summary:** SDN flow-table translation delivers near-linear throughput scaling with low control-plane overhead.
