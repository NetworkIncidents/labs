#!/usr/bin/env bash
# A power cut: the server comes back with a new address (a new DHCP lease) and the router restarts with an empty
# neighbour table. The router's port forward still points at the server's old address.
set -euo pipefail
S=clab-port-forward-server
docker exec $S ip addr del 10.0.10.50/24 dev eth1
docker exec $S ip addr add 10.0.10.51/24 dev eth1
docker exec $S ip route replace default via 10.0.10.1 dev eth1
docker exec clab-port-forward-router ip neigh flush dev eth2
