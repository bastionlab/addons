# Bastion marketplace

The add-ons, skins, widget packs and designs for [Bastion](https://github.com/bastionlab/core), the
self-hosted control panel for your home server. Every Bastion install reads this repository's `index.json`
and shows it on its Add-ons page.

Anyone can publish here. An automatic check reviews every submission, and you can only publish and update
your own work.

## What lives here

| Kind | What it is | Where |
|---|---|---|
| **Add-on** | A page, integration or tool: a manifest, a web part and optionally host code | `<id>/` |
| **Skin** | A full visual makeover: navigation, panels, backdrop | `skin-<name>/` (an add-on) |
| **Widget pack** | Ready-made widgets for Home, declared in JSON | `<id>/` with `kind: widget` |
| **Design** | A colour theme: tokens, radius, light and dark | `_designs/<slug>.json` |

`index.json` is generated from these folders by `build-index.py`; never edit it by hand.

## Building an add-on

### 1. Start from the template

In a Bastion install (the core repository on your host):

```sh
templates/new-addon my-addon "My add-on"
```

This creates `addons/my-addon/`:

```
my-addon/
├── addon.yaml          what the Add-ons page shows, plus routes, needs and roles
├── web/                a Nuxt layer the dashboard extends
│   ├── nuxt.config.ts
│   ├── app/pages/my-addon.vue
│   └── server/api/my-addon.get.ts
└── agent/my-addon.py   optional host code, through dash_sdk
```

Optional extras: `install.sh` (runs once as root when someone installs it, e.g. to create a container),
`deploy.sh` (runs on every deploy), `README.md` and `LICENSE`.

### 2. Describe it in `addon.yaml`

```yaml
id: my-addon
name: My add-on
icon: sparkles
author: your-github-login      # must be the account that publishes it
version: 0.1.0                 # x.y.z, raise it on every release
license: MIT                   # any SPDX id
desc: "One or two lines for the Add-ons card."
routes: [/my-addon]
needs: ""                      # e.g. "a GPU", "its own container"
depends_on: []                 # other add-ons it requires
warning: ""                    # terms-of-service or similar risks, shown before install
```

The full list of fields (home cards, settings, connections, roles, command palette entries, apps) is in the
core's [build rules](https://github.com/bastionlab/core/blob/main/.claude/rules/build.md#add-ons).

### 3. Develop it live

Your install picks up changes on save: web changes rebuild the app in seconds, Python changes restart the
agent. Use the core's components and helpers (`Panel`, `useActions`, `agentCall`, `upstream`) and its design
tokens rather than your own colours. Anything that changes the host must be an action the user confirms.

### 4. Check it locally

From this repository's root (`addons/` in your install):

```sh
python3 .github/check/check.py --id my-addon --pr .
```

This is the same check GitHub runs, without the linters.

### 5. Publish

Press **Publish** on the add-on's card on the Add-ons page. Bastion pushes the folder to a `publish/<id>`
branch, opens a pull request and waits for the check. Without the button: fork this repository, push your
folder to a branch named `publish/<id>` and open a pull request against `main`.

When every check is green, the pull request merges itself, `index.json` is rebuilt, and every install sees
your add-on within minutes. Installs with auto-update on get new versions within the hour.

## What the check looks at

| Check | Rule |
|---|---|
| Scope | The pull request only changes its own folder; never `index.json`, `.github/` or another add-on |
| Manifest | `addon.yaml` is complete, the id matches the folder, the version is higher than the published one |
| Owner | A new add-on's `author` is the account opening the pull request; an existing one can only be updated by its author |
| Safety | Reverse shells, miners, decode-and-run, planted SSH keys, reading other add-ons' or the dashboard's secrets, binaries, setuid, symlinks out, plus a ClamAV scan |
| Leaks | No tokens, keys or webhook URLs in the code |
| Style | No hardcoded colours, addresses or container ids; no native `alert()` or `confirm()`; files under 1 MB |
| Lint | ruff for Python, ESLint with the Vue plugin for the web part |

The report is posted on the pull request. Fix what it lists and push again; the check reruns by itself.

Every install also scans an add-on again before installing or updating it, and shows any warnings on the
confirm card. Treat host code with care: it runs as root on someone's server.

## Skins, widget packs and designs

- **Skins** are add-ons named `skin-<name>` that depend on `designs` and provide the skinnable pieces (navigation,
  backdrop, frame, panel, stat, topic card, page tabs). How to build one: [designs/SKINS.md](designs/SKINS.md).
- **Widget packs** are add-ons with `kind: widget` and a `widget.json`; see
  [widgets/examples/sample-pack](widgets/examples/sample-pack).
- **Designs** are made in the Designs page of your install and published from there. They go through a lighter
  check (known tokens only, under 4 kB, same ownership rule).

## Licensing

Each add-on chooses its own license in `addon.yaml`, shown on its card. Anything without its own license
falls under this repository's [AGPL-3.0](LICENSE).

## Questions and problems

Problems with a specific add-on: open an issue and mention the add-on's id, so its author sees it. Problems
with the marketplace itself or the check: [core issues](https://github.com/bastionlab/core/issues).
