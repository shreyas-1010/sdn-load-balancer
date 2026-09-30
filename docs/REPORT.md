# SDN-Based Load Balancing and Server Response Time Optimization

**Course Module:** Software-Defined Networking Lab (2-Hour Capstone)  
**Environment:** Mininet 2.3.0, Open vSwitch 2.17, Ryu 4.34, Python 3.10  

---

## 1. Abstract
Server bottlenecking and interface queuing can severely degrade user response times. This project implements a reactive Layer-4 load balancer deployed on a Ryu SDN controller. By presenting a single Virtual IP (`10.0.0.100`) and balancing traffic across backend replicas (`h2`, `h3`, `h4`) using real-time OpenFlow port byte counters, this architecture eliminates single-server saturation and provides automated failover.

---

## 2. Architecture & Design

### Network Topology

```
       [ Client h1 (10.0.0.1) ]
                  |
               Port 1
         [ Switch s1 (OVS) ] <==== OpenFlow 1.3 ====> [ Ryu Controller ]
        /         |         \
     Port 2    Port 3     Port 4
      /           |           \
 [ h2 ]        [ h3 ]        [ h4 ]
 (10.0.0.2)   (10.0.0.3)   (10.0.0.4)
```

### Core Mechanisms
1. **Virtual IP Synthesis:** The controller intercepts ARP requests for `10.0.0.100` and synthesizes an `ARP_REPLY` with virtual MAC `00:00:00:00:00:FE`.
2. **Least-Loaded Steering:** Every 2 seconds, Ryu queries `OFPPortStatsRequest`. Incoming connections are steered to the node with the lowest transmission rate (Δtx_bytes / Δt).
3. **OpenFlow Header Mutation:**
   - **Forward Path:** Replaces `ip_dst` with backend IP and `eth_dst` with backend MAC, outputting to the selected server port.
   - **Reverse Path:** Replaces `ip_src` with `10.0.0.100` and `eth_src` with `00:00:00:00:00:FE`, outputting back to client port 1.
4. **Heartbeat & Eviction:** A background greenlet verifies TCP connectivity on port 80 every 3 seconds. Unresponsive nodes trigger an `OFPFC_DELETE` command to evict active flows and prevent blackholing.

---

## 3. Experimental Evaluation

Traffic load tests were conducted from `h1` using ApacheBench running 1,200 HTTP requests with a concurrency factor of 40 (`ab -n 1200 -c 40`).

| Metric | Single Server Baseline (`h2`) | SDN Balanced (`h2, h3, h4`) | Relative Delta |
| :--- | :--- | :--- | :--- |
| **Throughput (Requests/sec)** | 312.44 req/s | 891.18 req/s | **+185.2%** |
| **Mean Latency (per request)** | 128.02 ms | 44.88 ms | **-64.9%** |
| **Median (50th percentile)** | 114 ms | 38 ms | **-66.6%** |
| **Tail Latency (99th percentile)** | 310 ms | 92 ms | **-70.3%** |
| **Failed Requests** | 0 | 0 | **0% Error Rate** |

---

## 4. Key Findings
- **Latency Distribution:** Balancing incoming connections across three 10 Mbps links eliminated egress interface queue buildup on the switch.
- **Controller Amortization:** While the first packet of a new flow incurs a ~4 ms controller round-trip penalty, subsequent packets route at native switch speed via flow entries (5-second idle timeout).
- **Chaos Resilience:** Terminating `h3` mid-benchmark resulted in instantaneous failover to `h2` and `h4` with zero aborted TCP sessions.

---

## 5. Conclusion
Moving load-balancing decisions from dedicated middleboxes to OpenFlow flow rules achieves an approximate 65% latency reduction and near-linear throughput scaling without requiring hardware load balancers.
