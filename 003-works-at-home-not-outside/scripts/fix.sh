#!/usr/bin/env bash
# Point the port forward at the server's new address (the same command the episode types on the router).
set -euo pipefail
docker exec clab-port-forward-router iptables -t nat -R PREROUTING 1 -i eth1 -p tcp --dport 8096 -j DNAT --to-destination 10.0.10.51:8096
