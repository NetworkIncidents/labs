#!/usr/bin/env bash
set -euo pipefail
docker exec clab-wrong-gateway-nas ip route replace default via 10.0.10.1 dev eth1
