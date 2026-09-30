<div align="center">

# SDN Load Balancer

*High-performance, fault-tolerant Layer-4 SDN load balancer built with Mininet & Ryu OpenFlow 1.3*

[![OpenFlow](https://img.shields.io/badge/OpenFlow-1.3-blue?style=flat-square)](#)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blueviolet?style=flat-square)](#)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](#)
[![Topology](https://img.shields.io/badge/Mininet-Emulated-orange?style=flat-square)](#)

</div>

---

## Highlights

- **Dynamic Least-Loaded Scheduling:** Queries real-time port transmission counters via `OFPPortStatsRequest` to balance traffic across the least saturated links.
- **Virtual IP Synthesis:** Responds to ARP queries for `10.0.0.100` dynamically, masking the backend farm behind a single virtual gateway.
- **Fault-Tolerant Self-Healing:** Background TCP probes detect server crashes and trigger proactive OpenFlow rule eviction (`OFPFC_DELETE`) within 3 seconds.
- **Wire-Speed Flow Execution:** Initial flow setup incurs a single controller round trip; subsequent packets route directly through the switch datapaths.

---

## Repository Layout

```
.
├── config/              # Centralized JSON runtime topology configs
├── docs/                # Architecture diagrams, academic report, and slides
├── scripts/             # Setup, automated benchmarking, chaos tests, and plotting
├── src/                 # Ryu controller and Mininet topology implementation
├── tests/               # Unit testing and probe validation suites
├── Makefile             # One-click command orchestration
└── requirements.txt     # Python dependencies
```

---

## Quickstart

### 1. Bootstrap System & Dependencies
```bash
make setup
```

### 2. Launch Controller (Terminal 1)

```bash
make controller
```

### 3. Launch Mininet Cluster (Terminal 2)

```bash
make topology
```

### 4. Execute Benchmark Suite

Inside the Mininet interactive prompt:

```bash
mininet> h1 bash scripts/benchmark.sh
```

### 5. Render Latency CDF Plots

On the host terminal:

```bash
make plot
```

---

## Benchmark Summary

| Metric | Single Server Baseline | SDN Balanced Cluster | Improvement |
| --- | --- | --- | --- |
| **Requests / Second** | `312.44 req/s` | `891.18 req/s` | **+185.2%** |
| **Mean Latency** | `128.02 ms` | `44.88 ms` | **-64.9%** |
| **99th Percentile** | `310.00 ms` | `92.00 ms` | **-70.3%** |

---

## Documentation Index

* Detailed pipeline diagrams: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
* Complete lab report: [`docs/REPORT.md`](docs/REPORT.md)
* Presentation slide deck: [`docs/PRESENTATION.md`](docs/PRESENTATION.md)

---

