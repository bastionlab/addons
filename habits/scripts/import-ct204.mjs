#!/usr/bin/env node
// ONE-TIME import of the old Habits app (CT 204, bastionlab/habits) into the native add-on's database.
//   node import-ct204.mjs <exported habits.db> [target db, default $NOTES_DIR or /var/lib/dash + /habits.db]
// The export is a copy of CT 204's /home/max/habits-data/habits.db (archived in
// /var/lib/dash-addons/old/habits-ct204-2026-10-27/habits.db). Reads it read-only; keeps live habits and the checks
// that are `done` for them (deleted habits and their checks are dropped). Idempotent: ids are kept, reruns change nothing.
// Run it where the target lives (CT 104, `node` there has node:sqlite), e.g. via `pct push` + `pct exec 104 -- node ...`.
import { DatabaseSync } from 'node:sqlite'
import { join } from 'node:path'

const [src, dst = join(process.env.NOTES_DIR || '/var/lib/dash', 'habits.db')] = process.argv.slice(2)
if (!src) { console.error('usage: import-ct204.mjs <exported habits.db> [target habits.db]'); process.exit(2) }

const old = new DatabaseSync(src, { readOnly: true })
const db = new DatabaseSync(dst)
db.exec(`
  PRAGMA journal_mode = WAL;
  CREATE TABLE IF NOT EXISTS habits (id TEXT PRIMARY KEY, title TEXT NOT NULL, freq TEXT NOT NULL, days TEXT NOT NULL,
    created INTEGER NOT NULL, updated INTEGER NOT NULL, deleted INTEGER NOT NULL DEFAULT 0);
  CREATE TABLE IF NOT EXISTS checks (habit_id TEXT NOT NULL, day TEXT NOT NULL, PRIMARY KEY (habit_id, day));
`)

const rows = old.prepare('SELECT kind, id, data, updated_at FROM items').all().map(r => ({ ...r, data: JSON.parse(r.data) }))
const live = rows.filter(r => r.kind === 'habit' && !r.data.deleted)
const ids = new Set(live.map(r => r.id))
const addHabit = db.prepare('INSERT OR IGNORE INTO habits (id, title, freq, days, created, updated, deleted) VALUES (?, ?, ?, ?, ?, ?, 0)')
const addCheck = db.prepare('INSERT OR IGNORE INTO checks (habit_id, day) VALUES (?, ?)')
let nh = 0, nc = 0, dropped = 0
db.exec('BEGIN')
for (const r of live) nh += Number(addHabit.run(r.id, r.data.title, r.data.freq, JSON.stringify(r.data.days), r.data.created, r.updated_at).changes)
for (const r of rows.filter(r => r.kind === 'check')) {
  if (!r.data.done) continue
  if (!ids.has(r.data.habit)) { dropped++; continue }
  nc += Number(addCheck.run(r.data.habit, r.data.date).changes)
}
db.exec('COMMIT')
console.log(`live habits in export: ${live.length}, added ${nh}; checks added ${nc}; done checks of deleted habits dropped ${dropped}`)
console.log(`now in ${dst}: ${db.prepare('SELECT COUNT(*) c FROM habits WHERE deleted = 0').get().c} habits, ${db.prepare('SELECT COUNT(*) c FROM checks').get().c} checks`)
