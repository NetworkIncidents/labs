#!/usr/bin/env bash
# Device can't leave its subnet - a Network Incidents lab (https://networkincidents.ca)
# Usage: ./lab.sh up | break | check | hint | fix | test | down | dashboard
# containerlab needs root unless your user can run it without sudo (containerlab's setup script sets that up).
set -euo pipefail
cd "$(dirname "$0")"
LAB=wrong-gateway
why=""
HINTS=(
  'Local traffic works and everything else doesn'"'"'t. Which device does the nas send traffic to when the address isn'"'"'t on its own network?'
  'ip route on the nas shows its default gateway. Is that the router'"'"'s address?'
  'ip neigh on the nas shows whether anything ever answered at that gateway address.'
  'The router is 10.0.10.1. ip route replace default via ... fixes it.'
)

healthy() {
  docker exec clab-wrong-gateway-nas ping -c 1 -W 1 10.0.20.80 2>&1 | grep -qP ' 0% packet loss' || { why='nas: ping -c 1 -W 1 10.0.20.80'; return 1; }
  docker exec clab-wrong-gateway-nas curl -s -m 5 http://10.0.20.80 2>&1 | grep -qP 'It works' || { why='nas: curl -s -m 5 http://10.0.20.80'; return 1; }
}

# wait_for healthy|broken SECONDS: poll until the lab is in that state, or give up
wait_for() {
  local deadline=$((SECONDS + $2))
  while :; do
    if healthy; then [[ $1 == healthy ]] && return 0; else [[ $1 == broken ]] && return 0; fi
    (( SECONDS < deadline )) || return 1
    sleep 1
  done
}

case "${1:-}" in
  up)
    containerlab deploy -t topology.clab.yml --reconfigure
    echo "Waiting for the lab to come up..."
    wait_for healthy 120 && echo "Lab is up and healthy. Next: ./lab.sh break" \
      || { echo "Lab came up but isn't healthy yet ($why). Try ./lab.sh check in a minute." >&2; exit 1; }
    rm -f .hint ;;
  break)
    echo "Breaking the lab (this can take up to 60 seconds)..."
    ./scripts/break.sh
    rm -f .hint
    echo "Broken. From the nas, curl http://10.0.20.80 times out, but ping 10.0.10.20 (the PC on its own network) works."
    echo "Find out why. ./lab.sh hint gives one hint at a time; ./lab.sh check tells you when it's fixed." ;;
  check)
    if healthy; then echo "Healthy: everything works."; else echo "Broken: $why"; exit 1; fi ;;
  hint)
    n=$(cat .hint 2>/dev/null || echo 0)
    if (( n >= ${#HINTS[@]} )); then echo "No more hints. ./lab.sh fix shows the fix (see scripts/fix.sh)."; exit 0; fi
    echo "Hint $((n + 1)) of ${#HINTS[@]}: ${HINTS[$n]}"
    echo $((n + 1)) > .hint ;;
  dashboard)   # optional: the live dashboard from the videos, at http://localhost:8090
    exec python3 ../dashboard/netviz_lab.py dashboard.json "${@:2}" ;;
  fix)
    ./scripts/fix.sh
    wait_for healthy 60 && echo "Fixed: everything works." || { echo "Still broken: $why" >&2; exit 1; } ;;
  test)   # what CI runs: up, break, broken, fix, healthy, down (./lab.sh: we're in the lab's folder now)
    ./lab.sh up
    ./lab.sh break
    wait_for broken 60 || { echo "FAIL: break didn't break it" >&2; exit 1; }
    ./lab.sh fix
    ./lab.sh down
    echo "PASS: $LAB" ;;
  down)
    containerlab destroy -t topology.clab.yml --cleanup
    rm -f .hint ;;
  *)
    sed -n '2,4p' "$0"; exit 2 ;;
esac
