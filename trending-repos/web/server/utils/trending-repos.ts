import { DatabaseSync } from 'node:sqlite'
import { join } from 'node:path'

/**
 * The Trending tab: once a day the agent (addons/trending-repos/agent/trending_repos.py) returns what is trending on GitHub today;
 * a few repos not seen before get their README read by the local model (summary, tags, "runs on my box?", a 0-100
 * fit against the owner's interests) and only the best fits are kept, so the feed gets a couple of new ones at a time. The rows live in CT 104 so they ride along in
 * the nightly backup.
 *
 * state: new → saved (To try) | dismissed; skipped = judged but not a top fit, never shown, kept so it isn't judged again
 */
const DIR = process.env.NOTES_DIR || '/var/lib/dash'
const db = new DatabaseSync(join(DIR, 'trending-repos.db'))
db.exec(`
  PRAGMA journal_mode = WAL;
  CREATE TABLE IF NOT EXISTS repos (
    repo TEXT PRIMARY KEY,
    descr TEXT NOT NULL DEFAULT '',
    lang TEXT NOT NULL DEFAULT '',
    stars INTEGER NOT NULL DEFAULT 0,
    gain INTEGER NOT NULL DEFAULT 0,
    sources TEXT NOT NULL DEFAULT '[]',
    summary TEXT,
    tags TEXT NOT NULL DEFAULT '[]',
    runs TEXT NOT NULL DEFAULT '',
    score INTEGER NOT NULL DEFAULT 0,
    readme TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT 'new',
    starred INTEGER NOT NULL DEFAULT 0,
    first_seen REAL NOT NULL,
    last_seen REAL NOT NULL
  );
  CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT NOT NULL);
`)

export const DEFAULT_INTERESTS = 'homelab, Proxmox, self-hosted, Docker, local AI, LLM, Ollama, Claude, AI agents, Nuxt, Vue, TypeScript, Python, dev tools, games, retro emulation'
const now = () => Date.now() / 1000
const kvGet = (k: string, d = '') => (db.prepare('SELECT v FROM kv WHERE k = ?').get(k) as any)?.v ?? d
const kvSet = (k: string, v: string) => db.prepare('INSERT INTO kv (k, v) VALUES (?, ?) ON CONFLICT(k) DO UPDATE SET v = excluded.v').run(k, v)

export const getInterests = () => kvGet('interests', DEFAULT_INTERESTS)
export function setInterests(text: string) {
  kvSet('interests', text.replace(/\s+/g, ' ').trim().slice(0, 600) || DEFAULT_INTERESTS)
}

const card = (r: any) => r && { ...r, sources: JSON.parse(r.sources || '[]'), tags: JSON.parse(r.tags || '[]'), readme: undefined, hasReadme: !!r.readme }
const COLS = 'repo, descr, lang, stars, gain, sources, summary, tags, runs, score, readme, state, starred, first_seen, last_seen'

export function listRepos(state: string) {
  const order = state === 'new' ? 'score DESC, gain DESC' : 'last_seen DESC'
  return db.prepare(`SELECT ${COLS} FROM repos WHERE state = ? ORDER BY ${order} LIMIT 200`).all(state).map(card)
}
export const getRepo = (repo: string) => db.prepare(`SELECT ${COLS} FROM repos WHERE repo = ?`).get(repo) as any
export const counts = () => Object.fromEntries((db.prepare('SELECT state, COUNT(*) n FROM repos GROUP BY state').all() as any[]).map(r => [r.state, r.n]))
export const status = () => ({ step: kvGet('step'), last: Number(kvGet('last', '0')), error: kvGet('error'), interests: getInterests() })

export function setState(repo: string, state: 'new' | 'saved' | 'dismissed') {
  db.prepare('UPDATE repos SET state = ? WHERE repo = ?').run(state, repo)
}
export const setStarred = (repo: string, on: boolean) => db.prepare('UPDATE repos SET starred = ? WHERE repo = ?').run(on ? 1 : 0, repo)

/** the best fresh matches for the Home card */
export const topRepos = (n = 3) =>
  db.prepare("SELECT repo, score FROM repos WHERE state = 'new' AND summary IS NOT NULL ORDER BY score DESC, gain DESC LIMIT ?").all(n)

const JUDGE = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    tags: { type: 'array', items: { type: 'string' } },
    runs: { type: 'string' },
    score: { type: 'integer' },
  },
  required: ['summary', 'tags', 'runs', 'score'],
}

async function judge(repo: string, descr: string, lang: string, readme: string, topics: string[]) {
  const out = await ollamaChat([{ role: 'user', content:
    `You help a homelab owner spot GitHub repos worth trying. Their box: Proxmox host, Docker containers, one NVIDIA RTX 3060 with 12 GB VRAM shared with Ollama, Nuxt/Vue and Python projects.\n`
    + `Their interests: ${getInterests()}\n\nRepo: ${repo} (${lang || 'language unknown'})\nGitHub description: ${descr}\nTopics: ${topics.join(', ')}\n\nREADME:\n${readme.slice(0, 7000)}\n\n`
    + `Answer as JSON:\n- summary: 2-3 plain sentences: what it is, what it is for, anything notable. No marketing words.\n`
    + `- tags: up to 4 short lowercase tags (for example self-hosted, ai, llm, homelab, dev tool, game, proxmox, cli, library).\n`
    + `- runs: one short line on how to run it (Docker, pip, npm, binary) and whether it needs a GPU or how much VRAM, judged against the 3060.\n`
    + `- score: 0-100 how well it fits the interests (90+ = clearly what they would love, 50 = loosely related, below 20 = unrelated).\n`
    + `Never use emoji or decorative symbols.` }], JUDGE, 'trending')
  const j = JSON.parse(out)
  return {
    summary: String(j.summary ?? '').trim().slice(0, 600),
    tags: (Array.isArray(j.tags) ? j.tags : []).map((t: any) => String(t).toLowerCase().slice(0, 24)).slice(0, 4),
    runs: String(j.runs ?? '').trim().slice(0, 200),
    score: Math.max(0, Math.min(100, Math.round(Number(j.score) || 0))),
  }
}

function agentGet<T = any>(path: string, timeout = 60_000) {
  const { agentUrl, agentToken } = useRuntimeConfig()
  return upstream<T>('agent', agentUrl, agentToken, path, timeout)
}
export function agentPost(path: string, body: any) {
  const { agentUrl, agentToken } = useRuntimeConfig()
  return upstream('agent', agentUrl, agentToken, path, 30_000, { method: 'POST', body })
}

const JUDGE_MAX = 10 // README reads per refresh: the local model is shared
const KEEP = 3 // how many of those make it into the feed
let busy = false
export const refreshing = () => busy

/** pull the candidate lists, judge repos not seen before, drop what fell off the lists long ago */
export async function refresh() {
  if (busy) return
  busy = true
  const step = (s: string) => kvSet('step', s)
  try {
    kvSet('error', '')
    step('Fetching lists')
    const got: any = await agentGet('/trending-repos/candidates')
    const list: any[] = got.repos ?? []
    if (!list.length) throw new Error(got.errors?.[0] || 'GitHub returned nothing')
    const t = now()
    const have = new Set((db.prepare('SELECT repo FROM repos').all() as any[]).map(r => r.repo))
    const fresh: any[] = []
    for (const r of list) {
      if (have.has(r.repo)) {
        db.prepare('UPDATE repos SET stars = ?, gain = ?, sources = ?, last_seen = ? WHERE repo = ?')
          .run(r.stars, r.gain, JSON.stringify(r.sources), t, r.repo)
      } else fresh.push(r)
    }
    fresh.sort((a, b) => (b.gain + b.stars / 50) - (a.gain + a.stars / 50))
    const judged: any[] = []
    let n = 0
    for (const r of fresh.slice(0, JUDGE_MAX)) {
      step(`Reading ${++n}/${Math.min(fresh.length, JUDGE_MAX)}: ${r.repo}`)
      try {
        const info: any = await agentGet(`/trending-repos/readme?repo=${encodeURIComponent(r.repo)}`, 30_000)
        judged.push({ r, info, j: await judge(r.repo, r.desc, r.lang || info.lang, info.readme || r.desc, info.topics ?? []) })
      } catch { /* one bad README must not stop the rest; it is tried again next refresh */ }
    }
    judged.sort((a, b) => b.j.score - a.j.score)
    judged.forEach(({ r, info, j }, i) => {
      db.prepare(`INSERT INTO repos (repo, descr, lang, stars, gain, sources, summary, tags, runs, score, readme, state, first_seen, last_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
        .run(r.repo, r.desc, r.lang || info.lang || '', r.stars, r.gain, JSON.stringify(r.sources), j.summary, JSON.stringify(j.tags), j.runs, j.score,
          String(info.readme ?? '').slice(0, 12000), i < KEEP ? 'new' : 'skipped', t, t)
    })
    // old unseen ones leave the feed
    db.prepare("DELETE FROM repos WHERE state IN ('new', 'skipped') AND last_seen < ?").run(t - 14 * 86400)
    kvSet('last', String(now()))
  } catch (e: any) {
    kvSet('error', String(e?.statusMessage || e?.message || e).slice(0, 200))
  } finally { step(''); busy = false }
}

/** called every 15 min by the plugin: refresh when the last one is over 22 h old */
export function maybeRefresh() {
  if (now() - Number(kvGet('last', '0')) > 22 * 3600) refresh()
}

/** a question about one repo, answered from its README by the local model */
export async function askRepo(repo: string, history: { role: string, content: string }[]) {
  const r = getRepo(repo)
  if (!r) throw createError({ statusCode: 404, statusMessage: 'no such repo' })
  const sys = `You answer questions about the GitHub repo ${repo} for a homelab owner (Proxmox host, Docker, one RTX 3060 12 GB shared with Ollama). `
    + `Use the README below; if it does not say, say you are not sure instead of guessing. Be short and concrete. Never use emoji or decorative symbols.\n\n`
    + `Summary: ${r.summary}\nREADME:\n${String(r.readme || r.descr).slice(0, 9000)}`
  const msgs = history.slice(-8).map(m => ({ role: m.role === 'assistant' ? 'assistant' : 'user', content: String(m.content).slice(0, 1500) }))
  return (await ollamaChat([{ role: 'system', content: sys }, ...msgs], undefined, 'trending')).trim()
}
