#!/usr/bin/env bash
# Split into VLANs, now nothing talks - a Network Incidents lab (https://networkincidents.ca)
# Usage: ./lab.sh up | break | check | hint | fix | test | down | dashboard
# containerlab needs root unless your user can run it without sudo (containerlab's setup script sets that up).
set -euo pipefail
cd "$(dirname "$0")"
LAB=vlan-trunk
why=""
HINTS=(
  'Start on the server'"'"'s side. Can the server reach its own gateway, 10.0.20.1? What does ip neigh say about it?'
  'The server can reach the NAS on the same VLAN, and the PC can reach its gateway on VLAN 10. So what'"'"'s different about VLAN 20'"'"'s way out?'
  'On the router, ip -br addr show type vlan lists its VLAN interfaces. Are both there?'
  'On the switch, bridge vlan show lists the VLANs each port carries. Which VLANs does eth1, the trunk to the router, carry?'
  'Put VLAN 20 on the trunk: bridge vlan add vid 20 dev eth1'
)

healthy() {
  docker exec clab-vlan-trunk-pc curl -s -m 3 http://10.0.20.80 2>&1 | grep -qP 'It works' || { why='pc: curl -s -m 3 http://10.0.20.80'; return 1; }
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
    echo "Broken. From the pc, curl -m 5 http://10.0.20.80 times out. The server and the NAS can still reach each other."
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
