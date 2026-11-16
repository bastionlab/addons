# Alert watch (a Bastion add-on)

This folder plugs into the Bastion core (`<paths.dashboard>` on the host). Before changing anything, read the
core's rules — they apply here too:
- `../../.claude/rules/design.md` — UI kit, phone-first (Android Chrome / Samsung Internet), copy, propose-and-approve for writes
- `../../.claude/rules/build.md` — add-on layout, `addon.yaml`, config instead of hardcoded IDs/IPs, `dash_sdk`

What it does: agent/alerts.py keeps `log` + `checked` in /var/lib/dash/alerts.json. Every minute the app
(`web/server/utils/alertwatch.ts`) looks for newly opened alerts and starts ONE read-only plan turn in the chat
"Alerts" (same pattern as chat tasks). Execute runs the existing plan -> execute flow; the Home card hands the
turn over through sessionStorage `bastion:exec`, never a URL parameter. State: alertwatch.json next to chats.db.
`agent/alertwatch.py` only reads alerts.json and the turn result files.

Layout: `addon.yaml` (manifest), `web/` (Nuxt layer: `app/pages`, `app/components`, `server/api`), `agent/*.py`.
Check: `python3 ../.github/check/check.py --id alertwatch --pr ..` from this folder.
