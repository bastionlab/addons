import { DatabaseSync } from 'node:sqlite'
import { join } from 'node:path'

/**
 * The Research tab: a question goes in, the local model plans sub-questions, searches SearXNG, reads the pages,
 * takes notes and writes a cited report. One run at a time, in this process (tick() from the plugin); the rows
 * live in CT 104 so they ride along in the nightly backup. A run that was going when the app restarted starts over.
 *
 * status: queued → running → done | failed | cancelled
 */
const DIR = process.env.NOTES_DIR || '/var/lib/dash'
const db = new DatabaseSync(join(DIR, 'research.db'))
db.exec(`
  PRAGMA journal_mode = WAL;
  CREATE TABLE IF NOT EXISTS research (
    id INTEGER PRIMARY KEY,
    question TEXT NOT NULL,
    depth TEXT NOT NULL,
    status TEXT NOT NULL,
    step TEXT NOT NULL DEFAULT '',
    sources TEXT NOT NULL DEFAULT '[]',
    report TEXT,
    error TEXT,
    created REAL NOT NULL,
    started REAL,
    finished REAL
  );
`)
db.prepare("UPDATE research SET status = 'queued', step = '' WHERE status = 'running'").run()

export const DEPTHS = {
  quick: { subs: 3, pages: 2, rounds: 1 },
  thorough: { subs: 4, pages: 3, rounds: 2 },
  overnight: { subs: 6, pages: 4, rounds: 3 },
} as const
export type Depth = keyof typeof DEPTHS

const now = () => Date.now() / 1000
const row = (r: any) => r && { ...r, sources: JSON.parse(r.sources || '[]') }

export const listResearch = () =>
  db.prepare('SELECT id, question, depth, status, step, sources, error, created, started, finished FROM research ORDER BY id DESC LIMIT 100')
    .all().map((r) => { const x = row(r); return { ...x, sources: undefined, nsources: x.sources.length } })
export const getResearch = (id: number) => row(db.prepare('SELECT * FROM research WHERE id = ?').get(id))

export function queueResearch(question: string, depth: Depth) {
  const { lastInsertRowid } = db.prepare("INSERT INTO research (question, depth, status, created) VALUES (?, ?, 'queued', ?)").run(question, depth, now())
  return getResearch(Number(lastInsertRowid))
}

const cancelled = new Set<number>()
export function cancelResearch(id: number) {
  const r = getResearch(id)
  if (r?.status === 'queued') db.prepare("UPDATE research SET status = 'cancelled', finished = ? WHERE id = ?").run(now(), id)
  else if (r?.status === 'running') cancelled.add(id)
}
export const deleteResearch = (id: number) => { if (getResearch(id)?.status !== 'running') db.prepare('DELETE FROM research WHERE id = ?').run(id) }

const set = (id: number, f: Record<string, any>) => {
  const cols = Object.keys(f)
  db.prepare(`UPDATE research SET ${cols.map(c => `${c} = ?`).join(', ')} WHERE id = ?`)
    .run(...cols.map(c => (typeof f[c] === 'object' && f[c] !== null ? JSON.stringify(f[c]) : f[c])), id)
}

const LIST = { type: 'object', properties: { questions: { type: 'array', items: { type: 'string' } } }, required: ['questions'] }
async function queries(prompt: string): Promise<string[]> {
  try { return (JSON.parse(await ollamaChat([{ role: 'user', content: prompt }], LIST, 'research')).questions ?? []).map(String).filter(Boolean) } catch { return [] }
}

async function run(id: number) {
  const job = getResearch(id)!
  const cfg = DEPTHS[job.depth as Depth] ?? DEPTHS.quick
  const step = (s: string) => { if (cancelled.has(id)) throw new Error('cancelled'); set(id, { step: s }) }
  const sources: { n: number, url: string, title: string }[] = []
  const notes: string[] = []
  const seen = new Set<string>()

  step('Planning')
  let queue = (await queries(`Break this research question into ${cfg.subs} specific web search queries that together cover it. Question: ${job.question}`)).slice(0, cfg.subs)
  if (!queue.length) queue = [job.question]

  for (let round = 1; round <= cfg.rounds && queue.length; round++) {
    for (const q of queue) {
      step(`Round ${round}/${cfg.rounds}: searching “${q.slice(0, 80)}”`)
      const found: any = await runTool('web_search', { query: q })
      const hits = (found.results ?? []).filter((h: any) => h.url && !seen.has(h.url)).slice(0, cfg.pages)
      for (const h of hits) {
        seen.add(h.url)
        step(`Round ${round}/${cfg.rounds}: reading ${new URL(h.url).hostname}`)
        const page: any = await runTool('fetch_page', { url: h.url })
        const text = String(page.text ?? '')
        if (page.error || text.length < 200) continue
        const out = await ollamaChat([{ role: 'user', content:
          `Question: ${job.question}\nSub-question: ${q}\n\nPage (${h.url}):\n${text}\n\nWrite 2-5 short bullet points with the facts from this page that help answer the question (numbers, names, dates). If the page has nothing useful, answer exactly: NONE.` }], undefined, 'research')
        if (/^\s*NONE\b/i.test(out)) continue
        const n = sources.push({ n: sources.length + 1, url: String(page.url ?? h.url), title: String(page.title ?? h.title ?? h.url).replace(/\s+/g, ' ').slice(0, 140) })
        notes.push(`[${n}] ${out.trim().slice(0, 1200)}`)
        set(id, { sources })
      }
    }
    queue = []
    if (round < cfg.rounds && notes.length) {
      step(`Round ${round}/${cfg.rounds}: finding gaps`)
      queue = (await queries(`Question: ${job.question}\n\nNotes so far:\n${notes.join('\n').slice(-6000)}\n\nWhat is still missing or uncertain? Give up to ${cfg.subs} new web search queries that fill the gaps, or an empty list if the notes are enough.`)).slice(0, cfg.subs)
    }
  }

  if (!notes.length) throw new Error('No useful pages found for this question.')
  step('Writing the report')
  const body = await ollamaChat([{ role: 'user', content:
    `Write a clear research report in Markdown that answers the question, using ONLY the numbered notes below. Cite sources inline as [1], [2]. Start with a 2-3 sentence answer, then sections with headings. Say where the notes disagree or leave gaps. Never use emoji, emoji in headings or decorative symbols. Do not invent sources.\n\nQuestion: ${job.question}\n\nNotes:\n${notes.join('\n\n').slice(0, 24000)}` }], undefined, 'research')
  const report = `${body.trim()}\n\n## Sources\n${sources.map(s => `${s.n}. [${s.title}](${s.url})`).join('\n')}\n`
  set(id, { status: 'done', report, step: '', finished: now(), sources })
}

let busy = false
export async function tick() {
  if (busy) return
  const next: any = db.prepare("SELECT id FROM research WHERE status = 'queued' ORDER BY id LIMIT 1").get()
  if (!next) return
  busy = true
  const id = next.id as number
  try {
    set(id, { status: 'running', started: now(), step: 'Starting' })
    await run(id)
  } catch (e: any) {
    const stop = e?.message === 'cancelled'
    set(id, { status: stop ? 'cancelled' : 'failed', error: stop ? null : String(e?.message ?? e).slice(0, 300), step: '', finished: now() })
  } finally { cancelled.delete(id); busy = false }
}
