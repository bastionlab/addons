#!/usr/bin/env bash
# run by the core's deploy.sh: put this add-on's gsm into the gameservers CT (if this box has one and it runs)
set -euo pipefail
HERE=$(dirname "$(readlink -f "$0")")
CT=$(jq -r '.cts.gameservers.id // empty' /etc/dash/config.json)
[ -n "$CT" ] && [ "$(pct status "$CT" 2>/dev/null | awk '{print $2}')" = running ] || exit 0
pct push "$CT" "$HERE/agent/gsm" /usr/local/bin/gsm --perms 755 && echo "   gsm → CT $CT"
