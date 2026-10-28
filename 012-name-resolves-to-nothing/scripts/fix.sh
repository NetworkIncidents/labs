#!/usr/bin/env bash
# The fix: the operator points db.homelab.test at the newest plan; then the guard.
set -euo pipefail
docker exec clab-dns-race-dns dnsctl repair db.homelab.test
docker exec clab-dns-race-dns dnsctl guard on
