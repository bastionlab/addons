# Mail add-on (v0.2)

Reads mail over IMAP into a small cache (`/var/lib/dash-mail/mail.db` on pve), sorts it into categories and summarises it with the
local model (Ollama), drafts three reply options on demand, and sends only when you tap Send and confirm.
Nothing is ever sent automatically. Passwords never leave the host and no route returns them.

## Accounts
Mail -> Accounts tab (`?s=accounts`). Each account is a card: name, address, status (Connected / Password missing /
Error), last sync, unread count, and Test / Edit / Remove (tap twice).

Add account: pick a provider (Gmail, Google Workspace, Microsoft 365, TU Berlin, GMX, web.de, Other), fill name, email,
username (defaults to the email) and password (write-only; when editing, leave blank to keep the saved one). Hosts and
ports come from the preset (under "Server settings"; editable for Other). Save logs in over IMAP and SMTP first (no mail
is sent); if that fails the exact error is shown with "Save anyway". Gmail/Workspace need an app password. TU Berlin
hosts (`imap.tu-berlin.de:993`, `smtp.tu-berlin.de:587`) are unverified.

Storage: rows in `/etc/dash/settings/mail.json` (`accounts_json`), passwords as `pw_<id>` in
`/etc/dash/secrets/mail.json`, both written by the add-on itself, 0600, atomic. The id is a slug of the name. Removing an
account deletes its secret and, by default, its cached mail. No route returns a password.

## Categories
Mail -> Categories (`?s=categories`). Seeded: Important, Later, Newsletter, Spam, Other (editable, can be turned off;
Other is the fallback and stays). Add your own, with a colour and a plain-words description the model reads.
- Rules (sender / domain / subject, first by order wins) sort without the model.
- Otherwise one qwen3.5:9b call gets the categories plus up to 8 of your recent hand corrections (same sender domain
  first) as examples. Unknown answers fall back to Other with confidence 0.
- Change a category in a message by hand: it is stored as an example and you can add "always sort mail from <domain>".
- Suggest categories proposes 3-6 new ones from recent mail (Accept saves). Re-sort mail clears auto-sorted mail
  (all, or only confidence < 0.6) and sorts it again; hand-sorted mail stays.
- Optional settings `judge_model` / `judge_below` (default 0.6): a second model re-checks unsure mail (source `judge`).
Tables `categories`, `rules`, `examples` and the `messages` columns `category`, `confidence`, `cat_source` are migrated
on first use; old `tags` are copied into `category`.

## Test
`python3 -I addons/mail/tests/test_mail.py` (parser, no network). `send` takes `dry_run: true` and prints instead of sending.
