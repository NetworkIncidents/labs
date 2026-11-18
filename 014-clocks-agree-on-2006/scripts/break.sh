#!/usr/bin/env bash
# The 2:50am chassis change, modelled: Melbourne's stratum 2 server goes off (the same chassis replacement turned it
# off), and the GPS card behind mel3 resets to the previous GPS epoch. Telstra's card went 1024 weeks back from
# 8 July 2026, to 22 November 2006; the lab's card jumps to that same date (at the current time of day).
set -euo pipefail
L=clab-clocks-agree-on-2006
docker exec $L-mel2 ip link set eth1 down
then="Nov 22, 2006 $(date -u +%H:%M:%S)"
docker exec $L-mel3 chronyc manual on >/dev/null
docker exec $L-mel3 chronyc settime "$then" >/dev/null
