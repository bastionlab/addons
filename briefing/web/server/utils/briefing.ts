import { DatabaseSync } from 'node:sqlite'
import { existsSync, mkdirSync } from 'node:fs'
import { join } from 'node:path'
import {
  type Facts, type HabitRow, type Lang, type SectionId, HUNT_KINDS, SECTION_IDS,
  afterRun, buildPrompt, calendarEvents, checkSummary, cutoffFor, dropSeeded, factsLine, habitFacts, huntFacts, huntUnreadable, isoDay,
  matches, nextAt, parseTime, rfc3339, shouldPush, shouldRun, weatherFacts,
} from './briefingCore'

/**
 * Daily briefing, the IO half (briefingCore.ts is the pure part): collects today's facts from what is installed and
 * switched on, lets the local model write two sentences about what matters (the facts line when it cannot),
 * stores the day in NOTES_DIR/briefing.db and pushes it once. Everything it needs from other add-ons comes through the
 * agent or the hunters' API; it never imports another add-on's code, so it works with any subset installed.
 */
const ID = 'briefing'
const DIR = process.env.NOTES_DIR || '/var/lib/dash'
const COLLECT_MS = 20_000
/** the system section runs alerts.problems() on the host: about 4 s measured, it shells out to pvesh and zpool */
const SYSTEM_MS = 30_000
const MODEL_MS = 120_000
/** a claim (the row's next_retry while a run is in progress) that this long has died */
const STALE_CLAIM_S = 15 * 60
const KEEP_DAYS = 30
/** what each hunter feed can return at most (the deals backend caps at 200, the others at 300 and 400) */
const FEED_LIMIT: Record<string, number> = { deals: 200, flats: 300, jobs: 300 }
const FEED_PATH: Record<string, string> = { deals: '/feed', flats: '/flats/feed', jobs: '/jobs/feed' }
/** the Ollama model when nothing usable is loaded */
const FALLBACK_MODEL = 'qwen3.5:9b'
/** add-on that provides a section; null = the core does */
const PROVIDER: Record<SectionId, string | null> = { calendar: 'calendar', mail: 'mail', deals: 'deals', flats: 'flats', jobs: 'jobs', habits: 'habits', system: null, weather: null }

export interface BriefingRow {
  day: string, created: number, facts: Facts, matters: SectionId[], summary: string, source: 'quiet' | 'model' | 'facts' | 'pending', pushed: number
  /** set only by a scheduled run that finished (forced runs leave it); 0 = the day is still open (pending or retrying unreadable sections) */
  scheduled_done: number, attempts: number, next_retry: number
}

// ---------------------------------------------------------------- store
let store: DatabaseSync | undefined
function db() {
  if (store) return store
  mkdirSync(DIR, { recursive: true })
  store = new DatabaseSync(join(DIR, 'briefing.db'))
  store.exec(`
    PRAGMA journal_mode = WAL;
    CREATE TABLE IF NOT EXISTS briefings (
      day TEXT PRIMARY KEY,           -- local YYYY-MM-DD
      created INTEGER NOT NULL,       -- epoch seconds; the next day's "new" starts here
      facts TEXT NOT NULL,            -- JSON
      matters TEXT NOT NULL,          -- JSON list of section ids
      summary TEXT NOT NULL,
      source TEXT NOT NULL,           -- pending | quiet | model | facts
      pushed INTEGER NOT NULL DEFAULT 0,
      scheduled_done INTEGER NOT NULL DEFAULT 1,  -- 1 once the scheduled run is final; only non-forced runs set it
      attempts INTEGER NOT NULL DEFAULT 0,        -- scheduled collections of the day
      next_retry INTEGER NOT NULL DEFAULT 0       -- epoch s: the next re-collection, or the end of a running claim
    );`)
  // a briefing.db made before these columns: its rows were all finished runs (DEFAULT 1); a run that was in flight is open
  const have = (store.prepare('PRAGMA table_info(briefings)').all() as any[]).map(c => c.name)
  for (const [col, def] of [['scheduled_done', 'INTEGER NOT NULL DEFAULT 1'], ['attempts', 'INTEGER NOT NULL DEFAULT 0'], ['next_retry', 'INTEGER NOT NULL DEFAULT 0']] as const) {
    if (!have.includes(col)) {
      store.exec(`ALTER TABLE briefings ADD COLUMN ${col} ${def}`)
      if (col === 'scheduled_done') store.exec("UPDATE briefings SET scheduled_done = 0 WHERE source = 'pending'")
    }
  }
  return store
}

const parse = (r: any): BriefingRow => ({ ...r, facts: JSON.parse(r.facts), matters: JSON.parse(r.matters) })
export function briefingFor(day: string): BriefingRow | null {
  const r = db().prepare('SELECT * FROM briefings WHERE day = ?').get(day)
  return r ? parse(r) : null
}

/**
 * Take today's row before collecting anything, so a restart or a second process cannot run (or push) it twice.
 * A claim is a lease in next_retry: no row = insert one (pending); an open row whose next_retry has passed (a retry is
 * due, or the run that held it died) = extend the lease. A finished row (scheduled_done = 1) is never claimed.
 */
function claim(day: string, nowSec: number): boolean {
  const d = db()
  d.exec('BEGIN IMMEDIATE')
  try {
    const r: any = d.prepare('SELECT scheduled_done, next_retry FROM briefings WHERE day = ?').get(day)
    let ok = false
    if (!r) { d.prepare("INSERT INTO briefings (day, created, facts, matters, summary, source, pushed, scheduled_done, attempts, next_retry) VALUES (?, ?, '{}', '[]', '', 'pending', 0, 0, 0, ?)").run(day, nowSec, nowSec + STALE_CLAIM_S); ok = true }
    else if (!r.scheduled_done && r.next_retry <= nowSec) { d.prepare('UPDATE briefings SET next_retry = ? WHERE day = ?').run(nowSec + STALE_CLAIM_S, day); ok = true }
    d.exec('COMMIT')
    return ok
  } catch (e) { d.exec('ROLLBACK'); throw e }
}

// ---------------------------------------------------------------- settings
export interface BriefingSettings { time: string, push: boolean, lang: Lang, location: string, sections: Record<string, boolean> }
export async function briefingSettings(): Promise<BriefingSettings> {
  // no fallback to defaults: a failed read throws, the tick logs it and tries again next minute, and nothing gets finished on guesses
  const s = await addonSettings(ID)
  return {
    time: parseTime(s.time), push: s.push !== false, lang: s.lang === 'de' ? 'de' : 'en', location: String(s.location ?? '').trim().slice(0, 80),
    sections: Object.fromEntries(SECTION_IDS.map(id => [id, s[`sec_${id}`] !== false])),
  }
}

/** installed and on (or core-provided), and the section's own toggle is on */
export function sectionsOn(set: BriefingSettings): SectionId[] {
  const have = allAddons().map(a => a.id), off = addonsOff()
  return SECTION_IDS.filter((id) => {
    const p = PROVIDER[id]
    return set.sections[id] && (!p || (have.includes(p) && !off.includes(p)))
  })
}

// ---------------------------------------------------------------- collectors
const within = <T>(p: Promise<T>, ms = COLLECT_MS): Promise<T> => Promise.race([p, new Promise<never>((_, rej) => setTimeout(() => rej(new Error('timed out')), ms))])
const call = <T = any>(path: string, opts: UpstreamOpts = {}) => agent<T>(undefined as any, path, { timeout: COLLECT_MS, ...opts })

/** `partial`: sections that returned what they could but could not be read in full; they join `unavailable` and keep their data */
type Ctx = { now: Date, set: BriefingSettings, cutoff: number, partial: Set<SectionId> }
const COLLECT: Record<SectionId, (c: Ctx) => Promise<any>> = {
  async calendar({ now, partial }) {
    const start = new Date(now.getFullYear(), now.getMonth(), now.getDate()), end = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1)
    const r: any = await call('/gcal/events', { query: { start: rfc3339(start), end: rfc3339(end) } })
    const items = Array.isArray(r?.events) ? r.events : []
    if (r?.ok === false || (r?.errors?.length && !items.length)) throw new Error('calendar unreadable')
    if (r?.errors?.length) partial.add('calendar') // an account failed: the events we got stay, the day is not called clear. The error text (it names the account) goes nowhere.
    return { events: calendarEvents(items) }
  },
  async mail({ partial }) {
    const [sum, st] = await Promise.allSettled([call('/mail/summary'), call('/mail/status')])
    if (sum.status === 'rejected') throw sum.reason
    // an account that cannot sync (last_error) makes the counts incomplete: keep them, but say so
    if (st.status === 'rejected' || (st.value?.accounts ?? []).some((a: any) => a?.last_error)) partial.add('mail')
    const r: any = sum.value
    return { unread: Number(r?.total_unread ?? 0), important: Number(r?.total_important_unread ?? 0) }
  },
  deals: huntCollector('deals'),
  flats: huntCollector('flats'),
  jobs: huntCollector('jobs'),
  async habits({ now }) {
    const file = join(DIR, 'habits.db')
    if (!existsSync(file)) return undefined
    const h = new DatabaseSync(file, { readOnly: true })
    try {
      const rows = h.prepare('SELECT id, title, freq, days, created FROM habits WHERE deleted = 0 ORDER BY created, rowid').all() as any[]
      const habits: HabitRow[] = rows.map(r => ({ id: r.id, title: r.title, freq: r.freq, days: JSON.parse(r.days), created: r.created }))
      const checks: Record<string, string[]> = {}
      for (const c of h.prepare('SELECT habit_id, day FROM checks').all() as any[]) (checks[c.habit_id] ??= []).push(c.day)
      return habitFacts(habits, checks, now)
    } finally { h.close() }
  },
  async system({ cutoff }) {
    // thresholds live in agent/alerts.py (alerts.json); this only reads what is open
    // alerts: the agent runs alerts.problems() live (not the ping bookkeeping in alerts.json); one-off backup task failures only count since the cutoff
    const [a, o] = await Promise.allSettled([call('/briefing/alerts', { query: { since: cutoff }, timeout: SYSTEM_MS }), call('/overview', { timeout: SYSTEM_MS })])
    if (a.status === 'rejected') throw a.reason
    const alerts = (Array.isArray(a.value?.alerts) ? a.value.alerts : []).map((x: unknown) => cleanLine(x)).filter(Boolean).slice(0, 5)
    const ov: any = o.status === 'fulfilled' ? o.value : {}
    const pools = (ov.pools ?? []).filter((p: any) => p?.size > 0).map((p: any) => ({ name: String(p.name), pct: Math.round(100 * p.alloc / p.size) })).sort((x: any, y: any) => y.pct - x.pct)
    const runs = (ov.backups?.vzdump ?? []).map((v: any) => (v?.run?.ok ? Number(v.run.time) : 0)).filter(Boolean)
    return { alerts, backupAgeH: runs.length ? Math.max(0, Math.round((Date.now() / 1000 - Math.max(...runs)) / 3600)) : null, fullestPool: pools[0] ?? null }
  },
  async weather({ set }) {
    const r: any = await runTool('weather', set.location ? { location: set.location } : {})
    const w = r?.error ? null : weatherFacts(r, set.lang)
    if (!w) throw new Error(r?.error || 'weather unreadable')
    return w
  },
}
const cleanLine = (x: unknown) => String(x ?? '').replace(/[*`]/g, '').replace(/\s+/g, ' ').trim().slice(0, 200)

const SEARCHES_PATH: Record<string, string> = { deals: '/searches', flats: '/flats/searches', jobs: '/jobs/searches' }
// the backends count "new since" themselves (passed, backfill hour excluded): exact, no feed cap
const NEW_COUNT_PATH: Record<string, string> = { deals: '/new-count', flats: '/flats/new-count', jobs: '/jobs/new-count' }
function huntCollector(kind: 'deals' | 'flats' | 'jobs') {
  return async ({ cutoff, partial }: Ctx) => {
    const limit = FEED_LIMIT[kind]!
    // show=passed is the hunters' own "worth a look" view: not rejected by the model, reserved, sold or thumbs-down
    const [feed, searches, counts, fresh] = await Promise.all([
      deals<any[]>(undefined as any, `${FEED_PATH[kind]}?show=passed&limit=${limit}`, { timeout: COLLECT_MS }),
      deals<any[]>(undefined as any, SEARCHES_PATH[kind]!, { timeout: COLLECT_MS }),
      // jobs group rows after the SQL LIMIT, so the row count says nothing about the cut-off; its own counts (distinct per search) do
      kind === 'jobs' ? deals<any>(undefined as any, '/jobs/counts?show=passed', { timeout: COLLECT_MS }) : undefined,
      deals<any>(undefined as any, `${NEW_COUNT_PATH[kind]}?since=${Math.floor(cutoff)}`, { timeout: COLLECT_MS }).catch(() => undefined),
    ])
    if (!Array.isArray(feed) || !Array.isArray(searches)) throw new Error('unexpected feed')
    const created = Object.fromEntries(searches.filter(s => typeof s?.created_at === 'number').map(s => [String(s.id), s.created_at as number]))
    const rows = dropSeeded(feed, created) // a new search's first hour is backfill, not news (the hunters' notifications skip it too)
    const capped = kind === 'jobs' ? Number(counts?.total ?? 0) > feed.length : feed.length >= limit
    const h = huntFacts(kind, rows, cutoff, limit, capped) // the feed still gives the top rows
    const exact = Number(fresh?.new)
    if (fresh && Number.isInteger(exact) && exact >= 0) return { ...h, new: exact, capped: false }
    // fallback, only when the count route failed (older backend): count from the feed
    if (huntUnreadable(h)) partial.add(kind) // cut off and nothing new in what we saw: "nothing new" cannot be said
    return h
  }
}

async function collect(ctx: Ctx): Promise<Facts> {
  const ids = sectionsOn(ctx.set)
  const done = await Promise.allSettled(ids.map(id => within(COLLECT[id](ctx), id === 'system' ? SYSTEM_MS : COLLECT_MS)))
  const facts: Facts = { unavailable: [] }
  ids.forEach((id, i) => {
    const r = done[i]!
    if (r.status === 'rejected') { facts.unavailable.push(id); console.warn(`[briefing] ${id}: ${(r.reason as Error)?.message}`); return }
    if (r.value !== undefined) (facts as any)[id] = r.value
    if (ctx.partial.has(id)) facts.unavailable.push(id)
  })
  return facts
}

// ---------------------------------------------------------------- the model
/** the loaded model (the job's own, else the warm one); if what jobModel finds is not in memory, the default rather than loading another */
async function pickBriefingModel(): Promise<string> {
  try {
    const m = await jobModel(ID)
    const ps: any = await $fetch('/api/ps', { baseURL: ollamaBase(), headers: { 'X-Job': 'dash' }, timeout: 10_000 })
    if (m && (ps?.models ?? []).some((x: any) => x.name === m)) return m
  } catch {}
  return FALLBACK_MODEL
}

export async function compose(facts: Facts, lang: Lang): Promise<{ summary: string, source: 'quiet' | 'model' | 'facts' }> {
  if (!matches(facts).length) return { summary: factsLine(facts, lang), source: 'quiet' }
  try {
    const r: any = await $fetch('/api/chat', {
      baseURL: ollamaBase(), headers: { 'X-Job': 'briefing' }, method: 'POST', timeout: MODEL_MS,
      body: { model: await pickBriefingModel(), stream: false, think: false, messages: buildPrompt(facts, lang), options: { temperature: 0.2 } },
    })
    const ok = checkSummary(r?.message?.content, facts)
    if (ok) return { summary: ok, source: 'model' }
  } catch (e: any) { console.warn(`[briefing] model: ${e?.message}`) }
  return { summary: factsLine(facts, lang), source: 'facts' }
}

// ---------------------------------------------------------------- the run
let running = false
/**
 * Make today's briefing. Without `force` it is the scheduled run: after the set time, once a day. A late run still
 * generates but only pushes inside the 2 h window. Sections that could not be read keep the day open (retry every 10 min
 * until 1 h after the set time, push held); then it finalizes with what it has. `force` rewrites today's facts and
 * summary with the same "new since" cutoff, never pushes, and leaves scheduled_done / attempts / pushed alone, so it
 * cannot use up or block the scheduled run and its push.
 */
export async function runBriefing(opts: { force?: boolean, now?: Date } = {}): Promise<BriefingRow | null> {
  if (running) return null
  running = true
  try {
    const now = opts.now ?? new Date(), nowSec = Math.floor(+now / 1000), day = isoDay(now)
    const set = await briefingSettings()
    const have = briefingFor(day)
    let forcedFirst = false
    if (!opts.force) {
      // taken = finished, or a run / retry lease that has not run out; an expired lease is a retry that is due (or a run that died)
      const taken = !!have && (!!have.scheduled_done || have.next_retry > nowSec)
      if (!shouldRun(now, set.time, taken)) return null
      if (!claim(day, nowSec)) return null
    } else if (!have) {
      if (!claim(day, nowSec)) return null
      forcedFirst = true
    } else if (have.source === 'pending' && have.next_retry > nowSec) return null // the scheduled run is writing it right now
    const prev: any = db().prepare("SELECT created FROM briefings WHERE day < ? AND source != 'pending' ORDER BY day DESC LIMIT 1").get(day)
    const facts = await collect({ now, set, cutoff: cutoffFor(nowSec, prev?.created ?? null), partial: new Set() })
    const m = matches(facts)
    const { summary, source } = await compose(facts, set.lang)
    const body = [JSON.stringify(facts), JSON.stringify(m), summary, source] as const
    let final = false
    if (opts.force) {
      // a forced run that created the row leaves it open and due, so the scheduled run still happens (and pushes)
      db().prepare('UPDATE briefings SET facts = ?, matters = ?, summary = ?, source = ?, next_retry = CASE WHEN ? THEN 0 ELSE next_retry END WHERE day = ?').run(...body, forcedFirst ? 1 : 0, day)
    } else {
      const out = afterRun(now, set.time, facts.unavailable.length)
      final = out.final
      db().prepare('UPDATE briefings SET facts = ?, matters = ?, summary = ?, source = ?, scheduled_done = ?, attempts = attempts + 1, next_retry = ? WHERE day = ?')
        .run(...body, final ? 1 : 0, out.retryAt ? Math.floor(out.retryAt / 1000) : 0, day)
    }
    db().prepare('DELETE FROM briefings WHERE day < ?').run(isoDay(new Date(+now - KEEP_DAYS * 86_400_000)))
    // pushed is set before sending: a crash between the two loses one push rather than sending it twice
    if (final && shouldPush(now, set.time, set.push, m.length) && db().prepare('UPDATE briefings SET pushed = 1 WHERE day = ? AND pushed = 0').run(day).changes) {
      try { await call('/briefing/push', { method: 'POST', body: { title: set.lang === 'de' ? 'Tagesbriefing' : 'Daily briefing', body: summary } }) }
      catch (e: any) { console.warn(`[briefing] push: ${e?.message}`) }
    }
    return briefingFor(day)
  } finally { running = false }
}

/** what GET /api/briefing returns */
export async function briefingView(now = new Date()) {
  const set = await briefingSettings()
  const row = briefingFor(isoDay(now))
  const pending = row?.source === 'pending'
  const open = !!row && !row.scheduled_done && !pending
  return {
    today: row && !pending ? row : null, running: running || pending,
    // an open day (unreadable sections) is retried at next_retry; a forced first row is due now
    nextAt: open ? Math.max(row!.next_retry * 1000, +now) : nextAt(now, set.time, !!row && (!!row.scheduled_done || pending)),
    time: set.time, lang: set.lang, available: sectionsOn(set), hunters: HUNT_KINDS,
  }
}
