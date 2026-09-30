#!/bin/bash
set -e

echo "=== [1/3] Updating system packages ==="
sudo apt-get update -qq

echo "=== [2/3] Installing core SDN utilities ==="
sudo apt-get install -y mininet openvswitch-switch apache2-utils python3-pip curl

echo "=== [3/3] Installing Python libraries ==="
pip3 install -r requirements.txt

echo "=== Starting Open vSwitch daemon ==="
sudo service openvswitch-switch start || sudo systemctl start openvswitch-switch

echo ">>> Environment setup complete."
