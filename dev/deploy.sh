#!/usr/bin/env bash
# run by the core's deploy.sh: refresh the pv helper in every running dev box (CTs tagged "dev")
set -euo pipefail
PV="$(jq -r '.paths.devbox // "/root/devbox"' /etc/dash/config.json)/pv"
[ -x "$PV" ] || { echo "   no $PV, skipping"; exit 0; }
for id in $(pvesh get /cluster/resources --type vm --output-format json | jq -r '.[] | select(.status=="running" and ((.tags // "") | split(";") | index("dev"))) | .vmid'); do
  pct push "$id" "$PV" /usr/local/bin/pv --perms 755 && echo "   pv → CT $id"
done
