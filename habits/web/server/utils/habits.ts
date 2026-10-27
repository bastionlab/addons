import { DatabaseSync } from 'node:sqlite'
import { join } from 'node:path'
import { randomUUID } from 'node:crypto'

/**
 * The Habits tab (2026-10-27, was an iframe of its own app in CT 204): a habit has a schedule (daily, weekly = one
 * weekday, or certain weekdays) and a set of days it was done. Streaks, hit rate and perfect days are worked out in
 * the page from this (utils/habits.ts) because "today" is the viewer's local day. Days are plain `YYYY-MM-DD`.
 * Habits are soft-deleted (their checks stay); a check row exists only while the day is done.
 * scripts/import-ct204.mjs loaded the old app's data once.
 */
export type Freq = 'daily' | 'weekly' | 'days'
export type Habit = { id: string, title: string, freq: Freq, days: number[], created: number }

const DIR = process.env.NOTES_DIR || '/var/lib/dash'
const db = new DatabaseSync(join(DIR, 'habits.db'))
db.exec(`
  PRAGMA journal_mode = WAL;
  CREATE TABLE IF NOT EXISTS habits (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    freq TEXT NOT NULL,            -- daily | weekly | days
    days TEXT NOT NULL,            -- JSON weekday list, 0 = Monday
    created INTEGER NOT NULL,      -- ms; history starts on this day
    updated INTEGER NOT NULL,
    deleted INTEGER NOT NULL DEFAULT 0
  );
  CREATE TABLE IF NOT EXISTS checks (
    habit_id TEXT NOT NULL,
    day TEXT NOT NULL,
    PRIMARY KEY (habit_id, day)
  );
`)

const bad = (m: string, code = 400) => createError({ statusCode: code, statusMessage: m })

export function parseDay(s: unknown): string {
  const d = String(s ?? '')
  if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) throw bad('bad day')
  const t = Date.parse(`${d}T12:00:00Z`)
  if (!Number.isFinite(t) || new Date(t).toISOString().slice(0, 10) !== d) throw bad('bad day')
  if (t > Date.now() + 36 * 3_600_000) throw bad('day is in the future')
  return d
}

function schedule(freq: unknown, days: unknown): { freq: Freq, days: number[] } {
  if (freq === 'daily') return { freq, days: [0, 1, 2, 3, 4, 5, 6] }
  if (freq !== 'weekly' && freq !== 'days') throw bad('bad schedule')
  const ds = [...new Set((Array.isArray(days) ? days : []).map(Number).filter(n => Number.isInteger(n) && n >= 0 && n <= 6))].sort()
  if (!ds.length) throw bad('pick a day')
  return { freq, days: freq === 'weekly' ? ds.slice(0, 1) : ds }
}

export function habitsOverview() {
  const rows = db.prepare('SELECT id, title, freq, days, created FROM habits WHERE deleted = 0 ORDER BY created, rowid').all() as any[]
  const habits: Habit[] = rows.map(r => ({ id: r.id, title: r.title, freq: r.freq, days: JSON.parse(r.days), created: r.created }))
  const checks: Record<string, string[]> = {}
  for (const c of db.prepare('SELECT c.habit_id h, c.day d FROM checks c JOIN habits x ON x.id = c.habit_id WHERE x.deleted = 0 ORDER BY c.day').all() as any[]) (checks[c.h] ??= []).push(c.d)
  return { habits, checks }
}

/** create (no id) or edit; the page may pick the id so an optimistic row keeps it */
export function saveHabit(b: any) {
  const title = String(b?.title ?? '').trim().slice(0, 120)
  if (!title) throw bad('name it')
  const s = schedule(b?.freq, b?.days)
  const id = b?.id ? String(b.id).slice(0, 64) : randomUUID()
  const now = Date.now()
  const cur = db.prepare('SELECT 1 FROM habits WHERE id = ? AND deleted = 0').get(id)
  if (cur) db.prepare('UPDATE habits SET title = ?, freq = ?, days = ?, updated = ? WHERE id = ?').run(title, s.freq, JSON.stringify(s.days), now, id)
  else db.prepare('INSERT OR REPLACE INTO habits (id, title, freq, days, created, updated, deleted) VALUES (?, ?, ?, ?, ?, ?, 0)').run(id, title, s.freq, JSON.stringify(s.days), now, now)
  return { id }
}

export function removeHabit(id: unknown) {
  db.prepare('UPDATE habits SET deleted = 1, updated = ? WHERE id = ?').run(Date.now(), String(id ?? ''))
  return { ok: true }
}

/** set (not flip) so a repeated or retried request can't undo itself */
export function setCheck(habit: unknown, day: unknown, done: unknown) {
  const h = String(habit ?? ''), d = parseDay(day)
  if (!db.prepare('SELECT 1 FROM habits WHERE id = ? AND deleted = 0').get(h)) throw bad('no such habit', 404)
  if (done) db.prepare('INSERT OR IGNORE INTO checks (habit_id, day) VALUES (?, ?)').run(h, d)
  else db.prepare('DELETE FROM checks WHERE habit_id = ? AND day = ?').run(h, d)
  return { ok: true }
}
