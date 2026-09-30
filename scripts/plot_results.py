#!/usr/bin/env python3
"""
Generates comparison graphs and CDF curves from ApacheBench raw outputs.
"""

import os
import matplotlib.pyplot as plt

RESULTS_DIR = "results"
BASELINE_TSV = os.path.join(RESULTS_DIR, "baseline_raw.tsv")
SDN_TSV = os.path.join(RESULTS_DIR, "sdn_raw.tsv")

def parse_tsv(filepath):
    if not os.path.exists(filepath):
        return []
    latencies = []
    with open(filepath, 'r') as f:
        next(f) # skip header
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 5:
                latencies.append(float(parts[4])) # ttime (total time in ms)
    return sorted(latencies)

def main():
    base_lats = parse_tsv(BASELINE_TSV)
    sdn_lats = parse_tsv(SDN_TSV)

    if not base_lats or not sdn_lats:
        print("Data files missing in results/. Run benchmark.sh first.")
        return

    plt.figure(figsize=(10, 5))

    # CDF Calculation
    base_cdf = [i / len(base_lats) for i in range(len(base_lats))]
    sdn_cdf = [i / len(sdn_lats) for i in range(len(sdn_lats))]

    plt.plot(base_lats, base_cdf, label="Baseline (Single Host h2)", color="#ff5555", linewidth=2)
    plt.plot(sdn_lats, sdn_cdf, label="SDN Balanced (Least-Loaded VIP)", color="#50fa7b", linewidth=2)

    plt.title("Latency Cumulative Distribution Function (CDF)", fontsize=14, pad=12)
    plt.xlabel("Total Request Time (ms)", fontsize=12)
    plt.ylabel("P(X <= x)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(fontsize=11)
    
    out_path = os.path.join(RESULTS_DIR, "latency_cdf.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"Chart successfully saved to {out_path}")

if __name__ == '__main__':
    main()
