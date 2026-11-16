#!/usr/bin/env bash
# The printer is given a static address by hand: the NAS's, 10.0.10.30. It announces it (as a device does when
# it brings an address up), so the PC's ARP entry for 10.0.10.30 now points at the printer's MAC.
set -euo pipefail
P=clab-dup-ip-printer
# A NAS that just served the PC still has a pending ARP check on it: a few seconds later it asks "who has
# 10.0.10.20? tell 10.0.10.30" from its own MAC, and the PC flips back. That's the fight itself; clearing it
# here (as on a NAS that's been idle a while) makes the fault show the same way every time.
docker exec clab-dup-ip-nas ip neigh flush dev eth1
docker exec $P ip addr add 10.0.10.30/24 dev eth1
docker exec $P arping -q -U -c 2 -I eth1 10.0.10.30 || true
