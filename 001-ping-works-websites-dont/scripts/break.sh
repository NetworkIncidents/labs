#!/usr/bin/env bash
# The homelab's DNS service dies; the box it runs on stays up.
set -euo pipefail
docker stop -t 2 clab-dns-down-coredns >/dev/null
