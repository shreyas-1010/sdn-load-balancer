#!/bin/bash
# Run from inside Mininet (h1 bash scripts/benchmark.sh)
set -e

RESULTS_DIR="results"
mkdir -p "$RESULTS_DIR"

echo "=========================================================="
echo " Starting Phase 1: Baseline Single Server (h2) "
echo "=========================================================="
ab -n 1200 -c 40 -g "$RESULTS_DIR/baseline_raw.tsv" http://10.0.0.2:80/ > "$RESULTS_DIR/baseline_ab.txt"

echo "=========================================================="
echo " Starting Phase 2: SDN Dynamic Balanced (VIP 10.0.0.100) "
echo "=========================================================="
ab -n 1200 -c 40 -g "$RESULTS_DIR/sdn_raw.tsv" http://10.0.0.100:80/ > "$RESULTS_DIR/sdn_ab.txt"

echo ""
echo "=========================================================="
echo "                   BENCHMARK SCORECARD                    "
echo "=========================================================="
echo ">>> BASELINE (Single Host h2):"
grep -E "(Requests per second|Time per request:|Transfer rate|Failed requests)" "$RESULTS_DIR/baseline_ab.txt"
echo ""
echo ">>> SDN BALANCED (VIP 10.0.0.100):"
grep -E "(Requests per second|Time per request:|Transfer rate|Failed requests)" "$RESULTS_DIR/sdn_ab.txt"
echo "=========================================================="
echo "Raw TSV dumps written to $RESULTS_DIR. Run 'make plot' to visualize."
