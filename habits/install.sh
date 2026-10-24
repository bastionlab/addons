#!/bin/sh
# runs once when Habits is installed from the marketplace: its backend (pvedash/habits) in a CT of its own
# (agent/backend-install leaves an already set-up CT alone)
exec "$(jq -r '.paths.dashboard // "/root/dashboard"' /etc/dash/config.json)/agent/backend-install" habits https://github.com/pvedash/habits habits 1024 8 nesting=1 tun
