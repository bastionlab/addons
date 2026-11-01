# Retro games (a Bastion add-on)

Read the core's rules first: `../../.claude/rules/design.md` and `../../.claude/rules/build.md`.

- Library = `<games CT /games mp on the host>/roms/<system>/` (shared with Azahar's `/roms` in the games CT and its
  Samba share), saves = `.../retro-saves/<system>/<file>.srm|.state` (+ `.bak` = the one before).
- Player = `/api/retro/play` (plain HTML, EmulatorJS pinned in `server/api/retro/play.get.ts`, cores from its CDN).
  The in-game save (srm) syncs every 15 s and on leaving; the EmulatorJS Save/Load state buttons go to the server.
- 3DS isn't playable in a browser: those cards point at the Moonlight stream (Wolf + Azahar in the games CT).
- Catalogue = Homebrew Hub API + Retrobrews GitHub trees, cached a day in `/var/lib/dash-retro/catalog.json`.
