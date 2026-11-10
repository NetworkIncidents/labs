#!/usr/bin/env bash
# The trunk to the router stops carrying VLAN 20 (as when a VLAN is left off the uplink's tagged list).
set -euo pipefail
docker exec clab-vlan-trunk-sw bridge vlan del vid 20 dev eth1
