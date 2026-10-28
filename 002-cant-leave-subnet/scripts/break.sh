#!/usr/bin/env bash
# The nas's default gateway is set to 10.0.10.254, where nothing answers (a typo, or an old router's address).
set -euo pipefail
docker exec clab-wrong-gateway-nas ip route replace default via 10.0.10.254 dev eth1
