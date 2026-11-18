#!/usr/bin/env bash
# Take the GPS card out of mel3's sources: make it a client of the national reference again, and bring mel2 back.
set -euo pipefail
L=clab-clocks-agree-on-2006
docker exec $L-mel3 chronyc add server 10.0.40.10 iburst minpoll 0 maxpoll 1 >/dev/null
docker exec $L-mel2 ip link set eth1 up
