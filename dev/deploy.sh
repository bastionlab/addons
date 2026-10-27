#!/usr/bin/env bash
# run by the core's deploy.sh: refresh the pv helper in every running dev box (CTs tagged "dev")
set -euo pipefail
PV="$(jq -r '.paths.devbox // "/root/devbox"' /etc/dash/config.json)/pv"
[ -x "$PV" ] || { echo "   no $PV, skipping"; exit 0; }
for id in $(pvesh get /cluster/resources --type vm --output-format json | jq -r '.[] | select(.status=="running" and ((.tags // "") | split(";") | index("dev"))) | .vmid'); do
  pct push "$id" "$PV" /usr/local/bin/pv --perms 755 && echo "   pv → CT $id"
done

# share links: dash-share in the dashboard CT, its public side behind Tailscale Funnel on :8443 (the dashboard on :443 stays tailnet-only)
DASH="$(jq -r '.cts.dash.id // 104' /etc/dash/config.json)"
HERE="$(cd "$(dirname "$0")" && pwd)"
pct exec "$DASH" -- mkdir -p /opt/dash-share
pct push "$DASH" "$HERE/share/share.mjs" /opt/dash-share/share.mjs
pct push "$DASH" "$HERE/share/dash-share.service" /etc/systemd/system/dash-share.service
pct exec "$DASH" -- sh -c 'systemctl daemon-reload && systemctl enable -q dash-share && systemctl restart dash-share' && echo "   dash-share → CT $DASH"
pct exec "$DASH" -- tailscale funnel status --json 2>/dev/null | jq -e '.AllowFunnel // {} | keys | any(endswith(":8443"))' >/dev/null \
  || echo "   share links stay closed until you run once: pct exec $DASH -- tailscale funnel --bg --https=8443 http://127.0.0.1:3100"
