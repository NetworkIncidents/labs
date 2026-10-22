#!/usr/bin/env bash
# The generator's database gets a permissions change: the featuregen user is granted `r0`, so its query (no
# database filter) returns every feature twice. It reaches replica-b first: files come out good and bad in turn
# (v3 good, v4 bad, v5 good, v6 bad), then replica-a too: every file is bad from v7. The generator is restarted
# with a clean history first, so the version numbers are the same every time (last good file: v5).
set -euo pipefail
L=clab-feature-limit
G=$L-gen

# wait (up to $2 seconds) until the generator's log has a line matching $1
wait_log() {
  local deadline=$((SECONDS + $2))
  until docker exec $G grep -q "$1" /var/log/featuregen.log 2>/dev/null; do
    (( SECONDS < deadline )) || { echo "break.sh: timed out waiting for '$1'" >&2; exit 1; }
    sleep 0.2
  done
}
grant() {
  docker exec $G python3 -c "import sqlite3; d = sqlite3.connect('/data/$1.db'); \
d.execute(\"INSERT INTO grants VALUES ('featuregen', 'r0')\"); d.commit()"
}

docker exec $G pkill -f 'featuregen run' || true
docker exec $G sh -c 'rm -rf /var/lib/featuregen /var/log/featuregen.log'
for e in edge1 edge2 edge3; do docker exec $L-$e sh -c ': > /var/log/proxy.log'; done
docker exec $G featuregen start >/dev/null

wait_log '^.* v2 ' 60
grant replica-b
wait_log '^.* v6 ' 120
grant replica-a
wait_log '^.* v9 ' 90
