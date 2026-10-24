# pvedash add-ons

The marketplace for [pvedash](https://github.com/pvedash): one folder per add-on, plus `index.json`.

- `<id>/addon.yaml`: what the Add-ons page shows (name, author, version, description, needs, dependencies)
- `<id>/web/`: a Nuxt layer the dashboard extends (pages, components, server routes)
- `<id>/agent/*.py`: host-side code, loaded by the dashboard agent through `dash_sdk`
- `<id>/install.sh` (optional): runs once as root on install, e.g. to create the add-on's CT

**Adding or updating one:** build it in your dashboard's `addons/<id>/`, then press **Publish** on its card in
`/addons`. That pushes the folder to a `publish/<id>` branch and opens a pull request; `.github/workflows/publish.yml`
checks it (only its own folder, manifest + higher version, author, malware scan + ClamAV, leaked secrets, style,
ruff + ESLint) and merges it when everything passes, then rebuilds `index.json`. Every dashboard installs the new
version within the hour (or on Refresh). Check locally first: `python3 .github/check/check.py --id <id> --pr .`
