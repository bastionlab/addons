# Widgets

Your own Home widgets, built inside Home's edit mode (Edit widgets opens a sheet) and shared as widget packs.

- Definitions: declarative JSON (`{id, name, size S|M|L, look, source, format}`), no code. Stored with `useSynced`
  (`widgets:defs`, `widgets:place:<phone|tablet|desktop>`), so they follow you across devices.
- Looks: number, sparkline, list, gauge, text, button.
- Sources: `api` (a GET `/api/...` path + optional dot-path), `metric` (dot-path into `/api/overview`), `service`
  (health of an app tile, from `/api/overview` services), `task` (latest answer of a scheduled chat task),
  `note` (a note's body). Buttons POST to a short allowlist (`/api/chat-tasks` run, `/api/net/speedtest`) after "Sure?".
- Describe-to-Claude: same job mechanism as Designs ("Describe a look"); the answer is validated, previewed, and only saved on Save.
- Widget packs: an add-on directory with `kind: widget` in `addon.yaml` and a `widget.json`; see `examples/sample-pack`.
  Install / update / remove them on /addons like any add-on. A pack may also ship Vue components
  (`web/app/components/Widget<Name>.global.vue`, definition look `component`); those pass the normal add-on scan
  on install. The builder never accepts pasted Vue code.

## v1 limits
- All your widgets sit as ONE block (one Home tile). You order them in the builder (Up / Down), not by dragging on Home.
- `/widgets` only redirects to Home; the add-on needs a route so its Home card can be switched on and off.
- Pack widgets are copied into your definitions when you add them; a pack update does not change widgets you already added.
