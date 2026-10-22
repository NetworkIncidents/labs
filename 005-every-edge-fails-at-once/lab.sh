#!/usr/bin/env bash
# Every edge fails at once - a Network Incidents lab (https://networkincidents.ca)
# Usage: ./lab.sh up | break | check | hint | fix | test | down
# containerlab needs root unless your user can run it without sudo (containerlab's setup script sets that up).
set -euo pipefail
cd "$(dirname "$0")"
LAB=feature-limit
why=""
HINTS=(
  'Is the origin itself fine? Ask it from an edge: curl http://10.0.20.80'
  'Each edge keeps a log of the feature files it loads: /var/log/proxy.log. Look at the rhythm.'
  'How many features are in the file the edges have now (/etc/proxy/features.txt), and how many are different?'
  'The generator (node gen) logs which replica each file came from: /var/log/featuregen.log'
  'Read the generator'"'"'s query (/opt/featuregen/query.sql), then compare it with what the replica shows: dbq replica-a "SELECT database, count(*) FROM system_columns GROUP BY database"'
  'To recover: stop the generator, then push a file that loaded fine (featuregen push /var/lib/featuregen/vN.txt). For good: fix the query, and restart the generator with --max-features 200 --canary edge1.'
)

healthy() {
  docker exec clab-feature-limit-client curl -s -m 3 http://10.0.20.11 2>&1 | grep -qP 'It works' || { why='client: curl -s -m 3 http://10.0.20.11'; return 1; }
  docker exec clab-feature-limit-client curl -s -m 3 http://10.0.20.12 2>&1 | grep -qP 'It works' || { why='client: curl -s -m 3 http://10.0.20.12'; return 1; }
  docker exec clab-feature-limit-client curl -s -m 3 http://10.0.20.13 2>&1 | grep -qP 'It works' || { why='client: curl -s -m 3 http://10.0.20.13'; return 1; }
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
    echo "Breaking the lab (this can take up to 240 seconds)..."
    ./scripts/break.sh
    rm -f .hint
    echo "Broken. From the client, all three edges (10.0.20.11-13) answer 500. Before that they failed and recovered in turn."
    echo "Find out why. ./lab.sh hint gives one hint at a time; ./lab.sh check tells you when it's fixed." ;;
  check)
    if healthy; then echo "Healthy: everything works."; else echo "Broken: $why"; exit 1; fi ;;
  hint)
    n=$(cat .hint 2>/dev/null || echo 0)
    if (( n >= ${#HINTS[@]} )); then echo "No more hints. ./lab.sh fix shows the fix (see scripts/fix.sh)."; exit 0; fi
    echo "Hint $((n + 1)) of ${#HINTS[@]}: ${HINTS[$n]}"
    echo $((n + 1)) > .hint ;;
  fix)
    ./scripts/fix.sh
    wait_for healthy 60 && echo "Fixed: everything works." || { echo "Still broken: $why" >&2; exit 1; } ;;
  test)   # what CI runs: up, break, broken, fix, healthy, down
    "$0" up
    "$0" break
    wait_for broken 60 || { echo "FAIL: break didn't break it" >&2; exit 1; }
    "$0" fix
    "$0" down
    echo "PASS: $LAB" ;;
  down)
    containerlab destroy -t topology.clab.yml --cleanup
    rm -f .hint ;;
  *)
    sed -n '2,4p' "$0"; exit 2 ;;
esac
