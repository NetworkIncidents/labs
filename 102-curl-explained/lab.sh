#!/usr/bin/env bash
# curl, explained - a Network Incidents lab (https://networkincidents.ca). Nothing is broken: it's for trying the commands.
# Usage: ./lab.sh up | check | test | down | dashboard
# containerlab needs root unless your user can run it without sudo (containerlab's setup script sets that up).
set -euo pipefail
cd "$(dirname "$0")"
LAB=curl-basics
why=""

healthy() {
  docker exec clab-curl-basics-pc curl -s -m 3 http://web.homelab.test 2>&1 | grep -qP 'It works' || { why='pc: curl -s -m 3 http://web.homelab.test'; return 1; }
}

wait_healthy() {
  local deadline=$((SECONDS + $1))
  until healthy; do (( SECONDS < deadline )) || return 1; sleep 1; done
}

case "${1:-}" in
  up)
    containerlab deploy -t topology.clab.yml --reconfigure
    echo "Waiting for the lab to come up..."
    wait_healthy 120 && echo "Lab is up. Open a shell (see README.md) and try the commands from the video." \
      || { echo "Lab came up but isn't ready yet ($why). Try ./lab.sh check in a minute." >&2; exit 1; } ;;
  check)
    if healthy; then echo "Ready: everything works."; else echo "Not ready: $why"; exit 1; fi ;;
  dashboard)   # optional: the live dashboard from the videos, at http://localhost:8090
    exec python3 ../dashboard/netviz_lab.py dashboard.json "${@:2}" ;;
  test)   # what CI runs: up, ready, down
    ./lab.sh up
    ./lab.sh down
    echo "PASS: $LAB" ;;
  down)
    containerlab destroy -t topology.clab.yml --cleanup ;;
  *)
    sed -n '2,4p' "$0"; exit 2 ;;
esac
