#!/bin/sh
# runs once when Money is installed from the marketplace: its backend (pvedash/money) in a CT of its own
# (agent/backend-install leaves an already set-up CT alone)
exec "$(jq -r '.paths.dashboard // "/root/dashboard"' /etc/dash/config.json)/agent/backend-install" money https://github.com/pvedash/money money 2048 12 nesting=1,keyctl=1
