#!/usr/bin/env bash
# run by the core's deploy.sh: install the Ollama logging proxy as its own unit, so agent restarts never cut Ollama
set -euo pipefail
HERE=$(dirname "$(readlink -f "$0")")
install -m 644 "$HERE/dash-cost-proxy.service" /etc/systemd/system/dash-cost-proxy.service
systemctl daemon-reload
systemctl enable dash-cost-proxy >/dev/null 2>&1
systemctl restart dash-cost-proxy && echo "   dash-cost-proxy → :11435"
