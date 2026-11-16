#!/usr/bin/env bash
# Two devices, one IP - a Network Incidents lab (https://networkincidents.ca)
# Usage: ./lab.sh up | break | check | hint | fix | test | down | dashboard
# containerlab needs root unless your user can run it without sudo (containerlab's setup script sets that up).
set -euo pipefail
cd "$(dirname "$0")"
LAB=dup-ip
why=""
HINTS=(
  'Ping works, so something answers at 10.0.10.30. Which device? On the pc, ip neigh shows the MAC address it has for it.'
  'On the nas, ip -br link show eth1 shows its own MAC. Does it match what the pc has?'
  'arping -b -c 2 -I eth1 10.0.10.30 on the pc prints every device that answers for that address. How many are there?'
  'On the switch, bridge fdb show br br0 shows which port each MAC was seen on, and so which device it is.'
  'Give the printer its own address: on the printer, ip addr del 10.0.10.30/24 dev eth1 and ip addr add 10.0.10.40/24 dev eth1. Then ip neigh flush dev eth1 on the pc.'
)

healthy() {
  docker exec clab-dup-ip-pc curl -s -m 3 http://10.0.10.30 2>&1 | grep -qP 'NAS: family photos' || { why='pc: curl -s -m 3 http://10.0.10.30'; return 1; }
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
    echo "Broken. From the pc, curl -s http://10.0.10.30 should show the NAS's page, but the printer's admin page comes back."
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
