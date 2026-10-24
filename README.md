# pvedash add-ons

The marketplace for [pvedash](https://github.com/pvedash): one folder per add-on, plus `index.json`.

- `<id>/addon.yaml`: what the Add-ons page shows (name, author, version, description, needs, dependencies)
- `<id>/web/`: a Nuxt layer the dashboard extends (pages, components, server routes)
- `<id>/agent/*.py`: host-side code, loaded by the dashboard agent through `dash_sdk`
- `<id>/install.sh` (optional): runs once as root on install, e.g. to create the add-on's CT

**Adding or updating one:** change the folder, bump `version:` in its `addon.yaml`, run `python3 build-index.py`,
and open a pull request. Once it's merged, every dashboard sees it on `/addons` (Install, or "update to vX").
