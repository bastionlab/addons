import { DatabaseSync } from 'node:sqlite'
import { join } from 'node:path'
import type { H3Event } from 'h3'

/**
 * Designs = a person's own set of the core's colour tokens (main.css) plus corner radius and light/dark.
 * Each account keeps its own designs and picks one (or a built-in) as its look; a design marked shared shows in
 * everyone's gallery, and people who use it follow the author's edits. Lives in CT 104 (/var/lib/dash/designs.db).
 */
const DIR = process.env.NOTES_DIR || '/var/lib/dash'
const db = new DatabaseSync(join(DIR, 'designs.db'))
db.exec(`
  PRAGMA journal_mode = WAL;
  CREATE TABLE IF NOT EXISTS designs (
    id INTEGER PRIMARY KEY,
    uid INTEGER NOT NULL,
    author TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL,
    tokens TEXT NOT NULL,
    shared INTEGER NOT NULL DEFAULT 0,
    created REAL NOT NULL,
    updated REAL NOT NULL
  );
  CREATE TABLE IF NOT EXISTS picks (uid INTEGER PRIMARY KEY, pick TEXT NOT NULL);
`)

export const COLOR_KEYS = ['bg', 'panel', 'panel-2', 'line', 'line-2', 'text', 'muted', 'faint', 'accent', 'ok', 'warn', 'bad', 'track', 'claude', 'term-bg', 'term-fg'] as const
export type Tokens = Record<string, string | number> & { radius: number, scheme: 'dark' | 'light' }

// the core's own look (main.css :root) and a few starting points; palettes, so hex is fine here
const DEFAULT: Tokens = {
  'bg': '#0a0c10', 'panel': '#11141a', 'panel-2': '#171b23', 'line': '#1f242e', 'line-2': '#2b313d',
  'text': '#e6e8ed', 'muted': '#8a92a2', 'faint': '#596070', 'accent': '#8ea6ff', 'ok': '#3ccf8e', 'warn': '#f0b440',
  'bad': '#f26b6b', 'track': '#1d222b', 'claude': '#d97757', 'term-bg': '#07090c', 'term-fg': '#d0d4dc', 'radius': 12, 'scheme': 'dark',
}
export const PRESETS: { key: string, name: string, tokens: Tokens }[] = [
  { key: 'default', name: 'Bastion', tokens: DEFAULT },
  { key: 'light', name: 'Daylight', tokens: { ...DEFAULT, 'bg': '#f4f5f8', 'panel': '#ffffff', 'panel-2': '#eef0f4', 'line': '#e2e5eb', 'line-2': '#cfd4dd', 'text': '#1b1f27', 'muted': '#5d6575', 'faint': '#8b93a3', 'accent': '#3d5eea', 'ok': '#18a36a', 'warn': '#c98a0b', 'bad': '#d94848', 'track': '#e4e7ed', 'term-bg': '#1b1f27', 'term-fg': '#e6e8ed', 'scheme': 'light' } },
  { key: 'forest', name: 'Forest', tokens: { ...DEFAULT, 'bg': '#0b100d', 'panel': '#111814', 'panel-2': '#17211b', 'line': '#1e2a23', 'line-2': '#2a3a30', 'text': '#e3ece6', 'muted': '#8a9c90', 'faint': '#5a6b60', 'accent': '#6fd39a', 'track': '#1a241e', 'term-bg': '#070b09' } },
  { key: 'dusk', name: 'Dusk', tokens: { ...DEFAULT, 'bg': '#100b14', 'panel': '#17111c', 'panel-2': '#1f1726', 'line': '#291f31', 'line-2': '#372a42', 'text': '#ece4f1', 'muted': '#9c8ca8', 'faint': '#6b5c77', 'accent': '#d08cff', 'track': '#231a2a', 'term-bg': '#0b070e', 'radius': 16 } },
  { key: 'contrast', name: 'High contrast', tokens: { ...DEFAULT, 'bg': '#000000', 'panel': '#0a0a0a', 'panel-2': '#141414', 'line': '#3a3a3a', 'line-2': '#5a5a5a', 'text': '#ffffff', 'muted': '#c8c8c8', 'faint': '#9a9a9a', 'accent': '#ffd400', 'track': '#262626', 'term-bg': '#000000', 'term-fg': '#ffffff', 'radius': 6 } },
]

const HEX = /^#[0-9a-f]{6}$/i
/** only known keys, strict #rrggbb colours and a sane radius: a shared design is applied in other people's browsers */
export function cleanTokens(t: any): Tokens {
  const out: any = { ...DEFAULT }
  for (const k of COLOR_KEYS) if (typeof t?.[k] === 'string' && HEX.test(t[k])) out[k] = t[k].toLowerCase()
  const r = Number(t?.radius)
  if (Number.isFinite(r)) out.radius = Math.max(0, Math.min(24, Math.round(r)))
  if (t?.scheme === 'light' || t?.scheme === 'dark') out.scheme = t.scheme
  return out
}

/** the account behind a request; PIN unlock and commands inside the CT are uid 0 (the owner) */
export const uidOf = (event: H3Event) => Number(event.context.uid ?? 0)
const nameOf = (uid: number) => (uid ? userById(uid)?.name : '') || 'owner'

const row = (r: any) => r && ({ id: r.id, uid: r.uid, author: r.author, name: r.name, tokens: cleanTokens(JSON.parse(r.tokens)), shared: !!r.shared, created: r.created, updated: r.updated })
const users = () => Object.fromEntries((db.prepare('SELECT pick, count(*) n FROM picks GROUP BY pick').all() as any[]).map(r => [r.pick, r.n]))

export const getDesign = (id: number) => row(db.prepare('SELECT * FROM designs WHERE id = ?').get(id))

export function listDesigns(uid: number) {
  const used = users()
  const withUse = (d: any) => ({ ...d, users: used[`d:${d.id}`] ?? 0 })
  return {
    mine: (db.prepare('SELECT * FROM designs WHERE uid = ? ORDER BY updated DESC').all(uid) as any[]).map(row).map(withUse),
    gallery: (db.prepare('SELECT * FROM designs WHERE shared = 1 AND uid != ? ORDER BY updated DESC').all(uid) as any[]).map(row).map(withUse),
    presets: PRESETS,
    pick: pickOf(uid),
  }
}

export function saveDesign(uid: number, b: any) {
  const name = String(b?.name ?? '').trim().slice(0, 40)
  if (!name) throw createError({ statusCode: 400, statusMessage: 'A name is needed' })
  const tokens = JSON.stringify(cleanTokens(b?.tokens))
  const now = Date.now() / 1000
  const id = Number(b?.id) || 0
  if (id) {
    const d = getDesign(id)
    if (!d || d.uid !== uid) throw createError({ statusCode: 404, statusMessage: 'Not your design' })
    db.prepare('UPDATE designs SET name = ?, tokens = ?, shared = ?, updated = ? WHERE id = ?').run(name, tokens, b?.shared ? 1 : 0, now, id)
    return getDesign(id)
  }
  const r = db.prepare('INSERT INTO designs (uid, author, name, tokens, shared, created, updated) VALUES (?, ?, ?, ?, ?, ?, ?)')
    .run(uid, nameOf(uid), name, tokens, b?.shared ? 1 : 0, now, now)
  return getDesign(Number(r.lastInsertRowid))
}

/** the author deletes their own; the owner may take down anyone's shared design */
export function deleteDesign(uid: number, id: number, isOwner: boolean) {
  const d = getDesign(id)
  if (!d || (d.uid !== uid && !isOwner)) throw createError({ statusCode: 404, statusMessage: 'Not your design' })
  db.prepare('DELETE FROM designs WHERE id = ?').run(id)
  db.prepare('DELETE FROM picks WHERE pick = ?').run(`d:${id}`)
}

/** a pick is `p:<preset>` or `d:<design id>`; the default look needs no row */
export const pickOf = (uid: number) => (db.prepare('SELECT pick FROM picks WHERE uid = ?').get(uid) as any)?.pick ?? 'p:default'

export function setPick(uid: number, pick: string) {
  const ok = /^p:/.test(pick) ? PRESETS.some(p => `p:${p.key}` === pick) : /^d:\d+$/.test(pick) && usable(uid, getDesign(Number(pick.slice(2))))
  if (!ok) throw createError({ statusCode: 400, statusMessage: 'Unknown design' })
  if (pick === 'p:default') db.prepare('DELETE FROM picks WHERE uid = ?').run(uid)
  else db.prepare('INSERT INTO picks (uid, pick) VALUES (?, ?) ON CONFLICT(uid) DO UPDATE SET pick = excluded.pick').run(uid, pick)
}

const usable = (uid: number, d: any) => !!d && (d.uid === uid || d.shared)

/** the tokens to paint for this person, or null for the stock look (also when the add-on is switched off) */
export function activeTokens(uid: number): Tokens | null {
  if (addonsOff().includes('designs')) return null
  const pick = pickOf(uid)
  if (pick.startsWith('p:')) return pick === 'p:default' ? null : PRESETS.find(p => `p:${p.key}` === pick)?.tokens ?? null
  const d = getDesign(Number(pick.slice(2)))
  return usable(uid, d) ? d.tokens : null
}
