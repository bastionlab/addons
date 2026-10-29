# Widget pack format (example, not an installed add-on)

A pack is a normal add-on folder in `addons/<id>/` with two things beyond the usual layout:

1. `addon.yaml` has `kind: widget` (the Widgets add-on lists these in Library; other keys as for any add-on)
2. `widget.json` next to it: an array (or `{ "widgets": [...] }`) of definitions. Ids are made unique by prefixing the pack id.

`sample-pack/` shows both. Copy it to `addons/<your-id>/`, rename, bump `version`, publish with the Publish button.
A pack with Vue components adds `web/nuxt.config.ts` and `web/app/components/Widget<Name>.global.vue`
and a definition `{ "look": "component", "component": "Widget<Name>" }`.
