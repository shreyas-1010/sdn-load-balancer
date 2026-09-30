.PHONY: all clean controller topology test benchmark plot help

SHELL := /bin/bash
PYTHON := python3

.DEFAULT_GOAL := help

help:
	@echo "SDN Load Balancer Automation Suite"
	@echo ""
	@echo "  make setup        Install system packages & python dependencies"
	@echo "  make controller   Run the Ryu SDN controller application"
	@echo "  make topology     Deploy the Mininet topology in CLI mode"
	@echo "  make plot         Generate latency & CDF distribution plots"
	@echo "  make test         Execute controller unit & health check tests"
	@echo "  make clean        Flush Mininet switches, OVS flows & dead procs"
	@echo ""

setup:
	@chmod +x scripts/*.sh
	@./scripts/setup_env.sh

controller:
	@echo ":: Launching Ryu SDN Controller..."
	ryu-manager src/controller.py --verbose

topology:
	@echo ":: Starting Mininet SDN Infrastructure..."
	sudo $(PYTHON) src/topology.py

plot:
	@echo ":: Rendering benchmark plots..."
	$(PYTHON) scripts/plot_results.py

test:
	@echo ":: Running Unit Tests..."
	$(PYTHON) -m unittest discover -s tests

clean:
	@echo ":: Purging Mininet runtime artifacts and hung sockets..."
	sudo mn -c 2>/dev/null || true
	sudo pkill -9 -f ryu-manager 2>/dev/null || true
	sudo pkill -9 -f "python3 -m http.server" 2>/dev/null || true
	sudo fuser -k 6633/tcp 2>/dev/null || true
	@echo ":: System state clean."
