#!/bin/sh
# runs once when the Hunters backend is installed from the marketplace: its backend (pvedash/deals) in a CT of its own
# (agent/backend-install leaves an already set-up CT alone)
exec "$(jq -r '.paths.dashboard // "/root/dashboard"' /etc/dash/config.json)/agent/backend-install" deals https://github.com/pvedash/deals deals 2048 12 nesting=1
