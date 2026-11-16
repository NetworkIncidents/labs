#!/usr/bin/env bash
# The fix: the printer gets its own address, and the PC forgets the wrong ARP entry.
set -euo pipefail
docker exec clab-dup-ip-printer ip addr del 10.0.10.30/24 dev eth1
docker exec clab-dup-ip-printer ip addr add 10.0.10.40/24 dev eth1
docker exec clab-dup-ip-pc ip neigh flush dev eth1
