#!/usr/bin/env bash
# The fix: stop the push, push the last good file (v5), run the generator with a size gate
# and a canary, filter the query to the `default` database.
set -euo pipefail
G=clab-feature-limit-gen
docker exec $G pkill -f 'featuregen run' || true
docker exec $G featuregen push /var/lib/featuregen/v5.txt
docker exec $G sed -i "s/^WHERE /WHERE database = 'default' AND /" /opt/featuregen/query.sql
docker exec $G featuregen start --max-features 200 --canary edge1
