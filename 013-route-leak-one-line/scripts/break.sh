#!/usr/bin/env bash
# The automated change from the post-mortem, modelled: retire site B's announcement from edge. The generated diff
# removes only the prefix-list line from term 20 of TO-TRANSIT, leaving "match ip next-hop prefix-list BACKBONE":
# every route edge learned from core, peer's 198.51.100.0/24 included, is now sent to transit.
set -euo pipefail
L=clab-route-leak
docker exec -i $L-edge sh -c 'cat > /var/log/policy-push.log' <<'LOG'
change 4127: stop announcing site B (192.0.2.128/25) to transit
generated diff for edge:
  route-map TO-TRANSIT permit 20
-  match ip address prefix-list SITE-B
pushed to edge: ok
LOG
docker exec $L-edge vtysh -c "conf t" -c "route-map TO-TRANSIT permit 20" \
  -c "no match ip address prefix-list SITE-B" -c "end" >/dev/null
