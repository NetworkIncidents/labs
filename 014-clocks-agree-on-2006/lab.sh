#!/usr/bin/env bash
# Every clock agrees on 2006 - a Network Incidents lab (https://networkincidents.ca)
# Usage: ./lab.sh up | break | check | hint | fix | test | down | dashboard
# containerlab needs root unless your user can run it without sudo (containerlab's setup script sets that up).
set -euo pipefail
cd "$(dirname "$0")"
LAB=clocks-agree-on-2006
why=""
HINTS=(
  'On mme, chronyc sources: which servers is it using, and which one has it marked x (outvoted)?'
  'On syd3, chronyc sources: is its stratum 2 server, mel2, answering? Who else does it listen to?'
  'On mel3, chronyc tracking: what is its reference, and what date does it give?'
  'Give mel3 the national reference instead of its GPS card: chronyc add server nmi iburst minpoll 0 maxpoll 1.'
  'Back on mme, chronyc tracking and chronyc sources: is the date 2026 again, and which sources does it use?'
)

healthy() {
  docker exec clab-clocks-agree-on-2006-mme chronyc tracking 2>&1 | grep -qP 'Ref time \(UTC\)\s*: .* 2026' || { why='mme: chronyc tracking'; return 1; }
  docker exec clab-clocks-agree-on-2006-syd3 chronyc sources 2>&1 | grep -qP 'mel2\s+2\s+\d+\s+377' || { why='syd3: chronyc sources'; return 1; }
  docker exec clab-clocks-agree-on-2006-perth3 chronyc sources 2>&1 | grep -qP '\^\* (syd2|mel2)' || { why='perth3: chronyc sources'; return 1; }
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
    echo "Broken. On mme, chronyc tracking says its reference time is in November 2006."
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
