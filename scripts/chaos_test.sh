#!/bin/bash
# Run on root terminal or client to test failover dynamics
set -e

echo "=== Dispatching 20 Requests across Cluster ==="
for i in {1..20}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 1 http://10.0.0.100:80/ || echo "FAIL")
    echo "[Req #$i] Status Code:$STATUS"
    sleep 0.3
done
echo "=== Chaos validation complete ==="
