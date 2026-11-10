#!/usr/bin/env bash
set -euo pipefail
docker exec clab-vlan-trunk-sw bridge vlan add vid 20 dev eth1
