import { DatabaseSync } from 'node:sqlite'
import { join } from 'node:path'
import deck from '../data/armenian.json'

/**
 * The Armenian tab (2026-10-27): Eastern Armenian as an Anki-style deck, the alphabet (group 0) first, then word packs
 * of ~50 (group 1, 2, …). Same scheduler as the Kanji tab: SM-2 learning steps 1 m / 10 m, graduate at 1 d (Easy 4 d),
 * ease 250 %, lapses relearn at 10 m and lose 20 % ease; days roll over at midnight Berlin. State lives here in CT 104
 * (armenian.db) so every device studies the same queue. The deck is built by scripts/build-armenian.py.
 *
 * state: new (no row) → learning → review ⇄ relearning
 *
 * Two directions only: the recognition card (`<id>`: Armenian → sound + meaning) and, once that has graduated, its
 * sibling write card (`w:<id>`: English meaning → the learner produces the Armenian).
 */
export type ArmCard = { id: string, t: 'l' | 'w', g: number, hy: string, tr: string, en: string[], cat: string, ex: [string, string, string] | null }
export const ARM_DECK = deck as ArmCard[]
const BY_K = new Map(ARM_DECK.map((x, i) => [x.id, { ...x, i }]))

const DIR = process.env.NOTES_DIR || '/var/lib/dash'
const db = new DatabaseSync(join(DIR, 'armenian.db'))
db.exec(`
  PRAGMA journal_mode = WAL;
  CREATE TABLE IF NOT EXISTS cards (
    k TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    due REAL NOT NULL,
    ivl INTEGER NOT NULL DEFAULT 0,
    ease REAL NOT NULL DEFAULT 2.5,
    step INTEGER NOT NULL DEFAULT 0,
    reps INTEGER NOT NULL DEFAULT 0,
    lapses INTEGER NOT NULL DEFAULT 0,
    added REAL NOT NULL
  );
  CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY,
    k TEXT NOT NULL,
    ts REAL NOT NULL,
    day TEXT NOT NULL,
    rating INTEGER NOT NULL,
    was TEXT NOT NULL,
    ivl INTEGER NOT NULL,
    secs REAL,
    prev TEXT
  );
  CREATE INDEX IF NOT EXISTS reviews_day ON reviews(day);
  CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
`)

const LEARN = [60, 600] // seconds
const RELEARN = [600]
const LEARN_AHEAD = 20 * 60 // like Anki: with nothing else left, learning cards due within 20 min come early
const MAX_IVL = 36500

const now = () => Date.now() / 1000
const berlinDay = (t: number) => new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Berlin' }).format(t)
/** the study day a moment belongs to: the Berlin calendar day */
export const armStudyDay = (t = now()) => berlinDay(t * 1000)
const dayNum = (d: string) => Math.floor(Date.parse(`${d}T12:00:00Z`) / 86_400_000)

// --- settings ---
const GROUPS = [...new Set(ARM_DECK.map(x => x.g))].sort((a, b) => a - b)
export type ArmSettings = { newPerDay: number, groups: number[], writing: boolean }
const DEFAULTS: ArmSettings = { newPerDay: 10, groups: [0, 1], writing: true }
export function armGetSettings(): ArmSettings {
  const s = { ...DEFAULTS }
  for (const r of db.prepare('SELECT key, value FROM settings').all() as any[]) try { (s as any)[r.key] = JSON.parse(r.value) } catch {}
  return s
}
export function armPutSettings(p: Partial<ArmSettings>) {
  const put = db.prepare('INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value')
  if (p.newPerDay != null) put.run('newPerDay', JSON.stringify(Math.max(0, Math.min(100, Math.round(p.newPerDay)))))
  if (p.writing != null) put.run('writing', JSON.stringify(!!p.writing))
  if (p.groups) {
    const l = [...new Set(p.groups.map(Number).filter(n => Number.isInteger(n) && GROUPS.includes(n)))].sort((a, b) => a - b)
    if (l.length) put.run('groups', JSON.stringify(l))
  }
  return armGetSettings()
}

// --- scheduling ---
const W = 'w:'
const base = (k: string) => (k.startsWith(W) ? k.slice(W.length) : k)
type Card = { k: string, state: string, due: number, ivl: number, ease: number, step: number, reps: number, lapses: number, added: number }
const getCard = (k: string) => db.prepare('SELECT * FROM cards WHERE k = ?').get(k) as Card | undefined
const fresh = (k: string): Card => ({ k, state: 'new', due: 0, ivl: 0, ease: 2.5, step: 0, reps: 0, lapses: 0, added: now() })

/** Anki adds a little randomness so cards learnt together don't stay bunched forever */
function fuzz(ivl: number) {
  if (ivl < 3) return ivl
  const d = Math.max(1, Math.round(ivl * 0.05))
  return ivl - d + Math.floor(Math.random() * (2 * d + 1))
}
const clampIvl = (n: number) => Math.min(MAX_IVL, Math.max(1, Math.round(n)))

/** what each button would do: the card after the answer */
function schedule(c: Card, rating: number, t = now()): Card {
  const n = { ...c, reps: c.reps + 1 }
  const steps = c.state === 'relearning' ? RELEARN : LEARN
  const review = (ivl: number) => Object.assign(n, { state: 'review', step: 0, ivl, due: t + ivl * 86400 })

  if (c.state === 'new' || c.state === 'learning' || c.state === 'relearning') {
    const step = c.state === 'new' ? 0 : c.step
    if (rating === 1) return Object.assign(n, { state: c.state === 'new' ? 'learning' : c.state, step: 0, due: t + steps[0] })
    if (rating === 2) {
      const wait = step === 0 && steps.length > 1 ? (steps[0] + steps[1]) / 2 : steps[step]
      return Object.assign(n, { state: c.state === 'new' ? 'learning' : c.state, step, due: t + wait })
    }
    if (rating === 3 && step + 1 < steps.length) return Object.assign(n, { state: c.state === 'new' ? 'learning' : c.state, step: step + 1, due: t + steps[step + 1] })
    if (c.state === 'relearning') return review(rating === 4 ? c.ivl + 1 : c.ivl)
    return review(rating === 4 ? 4 : 1)
  }

  // review
  const late = Math.max(0, dayNum(armStudyDay(t)) - dayNum(armStudyDay(c.due)))
  if (rating === 1) {
    return Object.assign(n, { state: 'relearning', step: 0, lapses: c.lapses + 1, ease: Math.max(1.3, c.ease - 0.2), ivl: 1, due: t + RELEARN[0] })
  }
  const hard = clampIvl(Math.max(c.ivl + 1, c.ivl * 1.2))
  if (rating === 2) { n.ease = Math.max(1.3, c.ease - 0.15); return review(fuzz(hard)) }
  const good = clampIvl(Math.max(hard + 1, (c.ivl + late / 2) * c.ease))
  if (rating === 3) return review(fuzz(good))
  n.ease = c.ease + 0.15
  return review(fuzz(clampIvl(Math.max(good + 1, (c.ivl + late) * c.ease * 1.3))))
}

/** the label under each answer button: "1m", "10m", "4d", "2.1mo" */
function span(c: Card, t: number) {
  const s = c.due - t
  if (s < 3600) return `${Math.max(1, Math.round(s / 60))}m`
  if (s < 86400) return `${Math.round(s / 3600)}h`
  const d = c.ivl || Math.round(s / 86400)
  if (d < 30) return `${d}d`
  if (d < 365) return `${(d / 30).toFixed(1).replace(/\.0$/, '')}mo`
  return `${(d / 365).toFixed(1).replace(/\.0$/, '')}y`
}

// --- the queue ---
const newToday = (day: string) => (db.prepare(`SELECT COUNT(*) n FROM reviews WHERE day = ? AND was = 'new'`).get(day) as any).n as number

function counts(t = now()) {
  const day = armStudyDay(t), s = armGetSettings()
  const cards = db.prepare('SELECT * FROM cards').all() as Card[]
  const seen = new Set(cards.map(c => c.k))
  const unseen = ARM_DECK.filter(x => s.groups.includes(x.g) && !seen.has(x.id))
  // write cards open up once the recognition card has graduated
  const graduated = new Set(cards.filter(c => c.state === 'review' && !c.k.startsWith(W)).map(c => c.k))
  const unseenWrite = s.writing ? ARM_DECK.filter(x => graduated.has(x.id) && s.groups.includes(x.g) && !seen.has(W + x.id)) : []
  const learnNow = cards.filter(c => (c.state === 'learning' || c.state === 'relearning') && c.due <= t)
  const learnToday = cards.filter(c => (c.state === 'learning' || c.state === 'relearning') && armStudyDay(c.due) <= day)
  const writeOk = (c: Card) => s.writing || !c.k.startsWith(W)
  const due = cards.filter(c => c.state === 'review' && armStudyDay(c.due) <= day && writeOk(c))
  const newDone = newToday(day)
  const newLeft = Math.min(unseen.length + unseenWrite.length, Math.max(0, s.newPerDay - newDone))
  return { day, s, cards, seen, unseen, unseenWrite, newDone, learnNow: learnNow.filter(writeOk), learnToday: learnToday.filter(writeOk), due, newLeft }
}

/** Anki's order: learning cards that are due, then reviews (with new cards spread among them), then learn-ahead */
export function armNextCard(t = now(), skip = '') {
  const q = counts(t)
  const pick = (list: Card[]) => list.filter(c => c.k !== skip).sort((a, b) => a.due - b.due)[0]
  let card = pick(q.learnNow)
  if (!card) {
    const rev = pick(q.due)
    const doneToday = (db.prepare(`SELECT COUNT(*) n FROM reviews WHERE day = ? AND was = 'review'`).get(q.day) as any).n as number
    // one new card every few reviews while both are left, so new cards don't all wait until the end
    const every = q.newLeft ? Math.max(1, Math.floor(q.due.length / q.newLeft)) : 0
    // new recognition and new write cards take turns
    const read = q.unseen.find(x => x.id !== skip)?.id, write = q.unseenWrite.map(x => W + x.id).find(k => k !== skip)
    const nw = !q.newLeft ? undefined : (q.newDone % 2 === 1 && write) || read || write
    if (nw && (!rev || (every && doneToday % (every + 1) === every))) card = fresh(nw)
    else card = rev
  }
  if (!card) card = pick(q.learnToday.filter(c => c.due <= t + LEARN_AHEAD))
  // the only card left is the one just answered: show it again rather than pretend we're done
  if (!card && skip) { const c = getCard(skip); if (c && c.state !== 'review' && c.due <= t + LEARN_AHEAD) card = c }

  const summary = {
    new: q.newLeft,
    learn: q.learnToday.length,
    review: q.due.length,
    // nothing to show yet but more learning steps later today
    wait: card ? 0 : Math.max(0, Math.round(Math.min(...q.learnToday.map(c => c.due), Infinity) - t)) || 0,
  }
  if (!card) return { card: null, ...summary }
  return { ...payload(card, t), ...summary }
}

function payload(card: Card, t: number) {
  const k = base(card.k), write = card.k.startsWith(W)
  return {
    card: {
      ...BY_K.get(k)!, kind: write ? 'write' : 'read', id: card.k, state: card.state, ivl: card.ivl, reps: card.reps, lapses: card.lapses,
    },
    buttons: [1, 2, 3, 4].map(r => span(schedule(card, r, t), t)),
  }
}

export function armAnswer(k: string, rating: number, secs: number | null) {
  if (!BY_K.has(base(k))) throw createError({ statusCode: 404, statusMessage: 'no such card' })
  if (![1, 2, 3, 4].includes(rating)) throw createError({ statusCode: 400, statusMessage: 'rating is 1 to 4' })
  const t = now()
  const before = getCard(k)
  const c = before ?? fresh(k)
  const n = schedule(c, rating, t)
  db.exec('BEGIN')
  try {
    db.prepare(`INSERT INTO cards (k, state, due, ivl, ease, step, reps, lapses, added) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(k) DO UPDATE SET state = excluded.state, due = excluded.due, ivl = excluded.ivl, ease = excluded.ease,
      step = excluded.step, reps = excluded.reps, lapses = excluded.lapses`)
      .run(k, n.state, n.due, n.ivl, n.ease, n.step, n.reps, n.lapses, n.added)
    db.prepare('INSERT INTO reviews (k, ts, day, rating, was, ivl, secs, prev) VALUES (?, ?, ?, ?, ?, ?, ?, ?)')
      .run(k, t, armStudyDay(t), rating, c.state, n.ivl, secs, before ? JSON.stringify(before) : null)
    db.exec('COMMIT')
  } catch (e) { db.exec('ROLLBACK'); throw e }
  return armNextCard(t, k)
}

/** Anki's undo: the last answer is taken back and its card comes up again */
export function armUndo() {
  const r = db.prepare('SELECT * FROM reviews ORDER BY id DESC LIMIT 1').get() as any
  if (!r) throw createError({ statusCode: 400, statusMessage: 'nothing to undo' })
  db.exec('BEGIN')
  try {
    if (r.prev) {
      const p = JSON.parse(r.prev) as Card
      db.prepare('UPDATE cards SET state = ?, due = ?, ivl = ?, ease = ?, step = ?, reps = ?, lapses = ? WHERE k = ?')
        .run(p.state, p.due, p.ivl, p.ease, p.step, p.reps, p.lapses, p.k)
    } else db.prepare('DELETE FROM cards WHERE k = ?').run(r.k)
    db.prepare('DELETE FROM reviews WHERE id = ?').run(r.id)
    db.exec('COMMIT')
  } catch (e) { db.exec('ROLLBACK'); throw e }
  const c = getCard(r.k) ?? fresh(r.k)
  const t = now()
  return { ...armNextCard(t), ...payload(c, t) }
}

/** back to new (the history stays for the heatmap) */
export function armForget(k: string) {
  db.prepare('DELETE FROM cards WHERE k IN (?, ?)').run(k, W + k)
  return { ok: true }
}

// --- progress ---
export function armenianOverview() {
  const t = now(), q = counts(t)
  const groups = GROUPS.map(g => ({ g, total: 0, seen: 0, mature: 0 }))
  const gr = (g: number) => groups[GROUPS.indexOf(g)]!
  for (const x of ARM_DECK) gr(x.g).total++
  // per card: 0 new, 1 learning, 2 young (< 21 d), 3 mature — the browse grid colours by it
  const status: Record<string, number> = {}
  for (const c of q.cards) {
    const x = BY_K.get(base(c.k))
    if (!x || c.k.startsWith(W)) continue
    const st = c.state === 'review' ? (c.ivl >= 21 ? 3 : 2) : 1
    status[c.k] = st
    gr(x.g).seen++
    if (st === 3) gr(x.g).mature++
  }
  const since = dayNum(q.day) - 182
  const days = db.prepare(`SELECT day, COUNT(*) n, SUM(rating > 1) ok, SUM(COALESCE(secs, 0)) secs FROM reviews GROUP BY day ORDER BY day`).all() as any[]
  const byDay: Record<string, number> = {}
  for (const d of days) if (dayNum(d.day) >= since) byDay[d.day] = d.n
  let streak = 0
  for (let d = dayNum(q.day) - (byDay[q.day] ? 0 : 1); ; d--) {
    const s = new Date(d * 86_400_000).toISOString().slice(0, 10)
    if (!days.some(x => x.day === s)) break
    streak++
  }
  const month = db.prepare(`SELECT COUNT(*) n, SUM(rating > 1) ok FROM reviews WHERE was = 'review' AND ts > ?`).get(t - 30 * 86400) as any
  const today = days.find(d => d.day === q.day)
  // reviews due per day for the next two weeks
  const forecast = Array.from({ length: 14 }, () => 0)
  for (const c of q.cards) if (c.state === 'review') forecast[Math.max(0, Math.min(13, dayNum(armStudyDay(c.due)) - dayNum(q.day)))]!++
  return {
    day: q.day,
    settings: q.s,
    groups,
    status,
    heat: byDay,
    streak,
    retention: month.n ? Math.round((100 * month.ok) / month.n) : null,
    today: { reviews: today?.n ?? 0, mins: Math.round((today?.secs ?? 0) / 60) },
    forecast,
    total: { seen: Object.keys(status).length, written: q.cards.filter(c => c.k.startsWith(W) && c.state === 'review').length, mature: Object.values(status).filter(x => x === 3).length, reviews: days.reduce((s, d) => s + d.n, 0) },
  }
}

export function armCardInfo(k: string) {
  const x = BY_K.get(k)
  if (!x) throw createError({ statusCode: 404, statusMessage: 'no such card' })
  const info = (c?: Card) => c ? { state: c.state, ivl: c.ivl, ease: Math.round(c.ease * 100), reps: c.reps, lapses: c.lapses, due: c.due } : null
  const hist = db.prepare('SELECT ts, rating, ivl, k LIKE \'w:%\' w FROM reviews WHERE k IN (?, ?) ORDER BY id DESC LIMIT 20').all(k, W + k)
  return { ...x, card: info(getCard(k)), write: info(getCard(W + k)), history: hist }
}
