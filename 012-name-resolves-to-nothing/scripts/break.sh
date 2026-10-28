#!/usr/bin/env bash
# The race from the post-mortem: enactor-a picks up a plan, checks once that it's newer, then is slow to write it
# (3 retries, 4 s apart). Meanwhile enactor-b applies newer plans and cleans up old ones. enactor-a writes its
# stale plan, the next clean-up deletes it, and db.homelab.test is left with no addresses, unable to take updates.
# Everything restarts first, so plan numbers are the same every run (the stale plan is 106).
set -euo pipefail
L=clab-dns-race

# wait (up to $3 s) until `docker exec $1 $2` prints something matching $4
wait_for() {
  local deadline=$((SECONDS + $3))
  until docker exec "$L-$1" sh -c "$2" 2>/dev/null | grep -qE "$4"; do
    (( SECONDS < deadline )) || { echo "break.sh: timed out waiting for '$4' on $1" >&2; exit 1; }
    sleep 0.2
  done
}
restart() {   # node, process pattern, start command
  # stop and start are separate execs: a pkill -f in the same shell line as the start command matches that shell
  docker exec "$L-$1" pkill -f "$2" || true
  sleep 0.3
  docker exec "$L-$1" sh -c "$3"
}

restart dns r53.py ': > /var/log/r53.log; nohup python3 /opt/lab/r53.py >/dev/null 2>&1 &'
restart planner planner.py 'nohup python3 /opt/lab/planner.py >/dev/null 2>&1 &'
for e in enactor-a enactor-b; do
  restart $e enactor.py ": > /var/log/enactor.log; rm -f /etc/enactor/slow; nohup python3 /opt/lab/enactor.py $e >/dev/null 2>&1 &"
done
wait_for dns 'dnsctl show' 30 'plan 10[5-9] '
docker exec $L-enactor-a enactorctl slow 3 4 >/dev/null
wait_for dns 'dnsctl show' 40 'NEEDS REPAIR'
