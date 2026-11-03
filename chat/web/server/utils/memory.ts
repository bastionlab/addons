import { DatabaseSync } from 'node:sqlite'
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'

/**
 * Chat memory (2026-10-27): short durable facts about the owner and the homelab. The newest/pinned ones are added to
 * the system prompt of every non-incognito chat turn (Claude and local). Facts only enter through the owner: /remember,
 * the Memory panel, or a "Remember this?" chip he tapped. Own db file, same directory as chats.db.
 */
const DIR = process.env.NOTES_DIR || '/var/lib/dash'
mkdirSync(DIR, { recursive: true })
const db = new DatabaseSync(join(DIR, 'memory.db'))
db.exec(`
  PRAGMA journal_mode = WAL;
  CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    src TEXT,
    at INTEGER NOT NULL,
    pinned INTEGER NOT NULL DEFAULT 0
  );
`)

export const MEM_MAX_FACTS = 200
export const MEM_MAX_TEXT = 300
const norm = (s: string) => s.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, ' ').trim()

export const cleanFact = (v: any) => String(v ?? '').replace(/\s+/g, ' ').trim().slice(0, MEM_MAX_TEXT)
const row = (r: any) => ({ id: r.id as number, text: r.text as string, src: (r.src ?? '') as string, at: r.at as number, pinned: !!r.pinned })

export const listFacts = () => (db.prepare('SELECT * FROM facts ORDER BY pinned DESC, at DESC, id DESC').all() as any[]).map(row)

/** same text, or one contained in the other (after lowercasing / dropping punctuation) */
export function isKnownFact(text: string) {
  const n = norm(text)
  if (!n) return false
  return listFacts().some((f) => { const m = norm(f.text); return m === n || (Math.min(m.length, n.length) >= 12 && (m.includes(n) || n.includes(m))) })
}

export function addFact(text: string, src = '') {
  const t = cleanFact(text)
  if (!t) throw createError({ statusCode: 400, statusMessage: 'empty fact' })
  if (isKnownFact(t)) return { ok: true, dup: true, facts: listFacts() }
  if ((db.prepare('SELECT count(*) AS n FROM facts').get() as any).n >= MEM_MAX_FACTS) throw createError({ statusCode: 400, statusMessage: `memory is full (${MEM_MAX_FACTS} facts), delete some first` })
  db.prepare('INSERT INTO facts (text, src, at) VALUES (?, ?, ?)').run(t, String(src).slice(0, 40), Date.now())
  return { ok: true, facts: listFacts() }
}

export function editFact(id: number, f: { text?: string, pinned?: boolean }) {
  if (f.text != null) {
    const t = cleanFact(f.text)
    if (!t) throw createError({ statusCode: 400, statusMessage: 'empty fact' })
    db.prepare('UPDATE facts SET text = ? WHERE id = ?').run(t, id)
  }
  if (f.pinned != null) db.prepare('UPDATE facts SET pinned = ? WHERE id = ?').run(f.pinned ? 1 : 0, id)
  return { ok: true, facts: listFacts() }
}

export function deleteFact(id: number) {
  db.prepare('DELETE FROM facts WHERE id = ?').run(id)
  return { ok: true, facts: listFacts() }
}

/** the text for the system prompt: pinned first, then newest; at most 20 facts and 1500 characters; '' when empty */
export function memoryPrompt(): string {
  const head = 'Remembered about the owner/server:'
  let out = head, n = 0
  for (const f of listFacts()) {
    const line = `\n- ${f.text}`
    if (n >= 20 || out.length + line.length > 1500) break
    out += line; n++
  }
  return n ? out : ''
}
