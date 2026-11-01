#!/usr/bin/env bash
# Revert the change by hand, as Cloudflare's operator did: put the prefix-list back in term 20 of TO-TRANSIT.
set -euo pipefail
L=clab-route-leak
docker exec $L-edge vtysh -c "conf t" -c "route-map TO-TRANSIT permit 20" \
  -c "match ip address prefix-list SITE-B" -c "end" >/dev/null
