# Files (a Bastion add-on)

Read the core's rules first: `../../.claude/rules/design.md` and `../../.claude/rules/build.md`.

- Roots = `/etc/dash/files.json` `{"roots":[{id,label,path,writable}]}`. Created on first use: `files` -> `/srv/bastion-files`
  (writable) plus read-only bookmarks for the games and media CT bind mounts. Every path is `realpath`-checked to stay
  inside its root; writes only on writable roots. Bookmarks are managed on the Bookmarks tab.
- Page links: `/files?r=<rootId>&p=<relative path>`; a file path opens its folder with the preview (chat file cards use this).
- Delete / rename are owner-run actions (`files_delete`, `files_rename`); upload is 8 MB chunks via `/api/files/upload`.
- Shares: `/var/lib/dash-files/shares.json` (0600) `{token:{root,p,expires,created}}`. The Funnel side (dash-share in the
  dashboard CT) serves `<funnel base>/f/<token>` by calling the agent's `GET /files/pub?t=<token>[&dl=1]` with Range forwarded.
  The base is the Dev add-on's share base (`https://<funnel host>:8443`).
- Containers: every CT is a virtual root `ct-<vmid>` (never stored; `pct list`, cached 15 s), path `/` = the CT's whole
  filesystem, always writable. Browse/raw/upload/mkdir/delete/rename run through `pct exec` (paths are argv, never
  interpolated); uploads take the folder's owner. No shares from CTs; top-level folders can't be deleted/renamed;
  stopped CTs error out (start them first).
