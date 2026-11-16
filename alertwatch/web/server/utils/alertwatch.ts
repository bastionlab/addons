import { existsSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import { randomUUID } from 'node:crypto'
import { join } from 'node:path'

/**
 * Alert watch: when agent/alerts.py opens a NEW alert (its `log` in /var/lib/dash/alerts.json, read through the agent's
 * /alertwatch/state), Claude looks into it read-only in the chat "Alerts" and proposes a fix as a plan turn; the
 * owner runs it with Execute (the chat's plan -> execute flow). Same pattern as chatTasks.ts runTask(). Times in the
 * alert log are unix seconds, everything this file stores is ms.
 */
export interface AlertEntry { key: string, msg: string, topic?: string, at: number, closed: number | null, oneoff?: boolean }
export interface AlertRun { id: string, keys: string[], msgs: string[], at: number, turn: string, session: string }
interface State { chat: string, runs: AlertRun[], lastByKey: Record<string, number> }

const FILE = join(process.env.NOTES_DIR || '/var/lib/dash', 'alertwatch.json')
const MAX_RUNS = 50
const WINDOW = 48 * 3_600_000

function load(): State {
  try {
    const s = existsSync(FILE) ? JSON.parse(readFileSync(FILE, 'utf8')) : {}
    return { chat: typeof s.chat === 'string' ? s.chat : '', runs: Array.isArray(s.runs) ? s.runs : [], lastByKey: s.lastByKey && typeof s.lastByKey === 'object' ? s.lastByKey : {} }
  } catch { return { chat: '', runs: [], lastByKey: {} } }
}
function save(s: State) {
  writeFileSync(FILE + '.tmp', JSON.stringify(s, null, 1))
  renameSync(FILE + '.tmp', FILE)
}
/** the Alerts chat id, made once */
function chatId(s: State) {
  if (!s.chat) { s.chat = 'k' + Math.random().toString(36).slice(2, 9); save(s) }
  return s.chat
}

const agent = <T>(path: string, opts: { method?: 'GET' | 'POST', body?: any, query?: any } = {}) => {
  const { agentUrl, agentToken } = useRuntimeConfig()
  return upstream<T>('agent', agentUrl, agentToken, path, 30_000, opts)
}
const plain = (m: string) => String(m ?? '').replace(/[*`]/g, '').replace(/\s+/g, ' ').trim()

function promptFor(entries: AlertEntry[]) {
  const list = entries.map(e => `- ${e.msg} (key ${e.key}, since ${new Date(e.at * 1000).toISOString()})`).join('\n')
  return `Bastion alert watch. These host alerts just opened on this Proxmox host:\n${list}\nInvestigate read-only with team mode (Haiku scouts for reading logs, containers and disks). Find the cause and check whether it is still happening. Your first line must be \`CAUSE: <one plain sentence>\`. If it has already cleared by itself and nothing needs doing, make the first line \`ALL-OK <one sentence>\` and stop. Otherwise propose the fix as numbered steps with the exact commands, and give each change its undo step. Keep it short; no emoji.`
}

/** start one read-only plan turn for these alerts and log it in the Alerts chat. Returns the run, or null when a turn is still going */
export async function investigateAlerts(entries: AlertEntry[], _force = false): Promise<AlertRun | null> {
  if (!entries.length) return null
  const cfg = await addonSettings('alertwatch')
  const model = ['sonnet', 'opus', 'haiku'].includes(cfg.model) ? cfg.model : 'sonnet'
  const effort = ['low', 'medium', 'high'].includes(cfg.effort) ? cfg.effort : 'medium'
  const s = load()
  const chat = chatId(s)
  // an unfinished turn from the last 3 h is still being worked on: skip (the agent refuses with `running` anyway)
  const prev = (chatById(chat) as any)?.turns?.at(-1)
  if (prev && prev.fin === false && Date.now() - prev.at < 3 * 3_600_000) return null
  const session = randomUUID()
  const r = await agent<{ turn?: string, running?: string }>('/claude/send', {
    method: 'POST', body: { chat, session, prompt: promptFor(entries), auto: false, plan: true, model, effort, team: true, quiet: true },
  })
  if (!r.turn) return null // a run is still going: nothing is marked, the next tick retries
  const now = Date.now()
  const run: AlertRun = { id: randomUUID().slice(0, 8), keys: entries.map(e => e.key), msgs: entries.map(e => plain(e.msg)), at: now, turn: r.turn, session }
  const fresh = load() // re-read: view() may have created the chat id meanwhile
  for (const k of run.keys) fresh.lastByKey[k] = now
  fresh.runs = [...fresh.runs, run].slice(-MAX_RUNS)
  fresh.chat = fresh.chat || chat
  save(fresh)
  const c: any = chatById(chat) ?? { id: chat, title: 'Alerts', at: 0, turns: [] }
  if (!c.folder) c.folder = TASKS_FOLDER
  c.turns.push({ q: 'Alert: ' + run.msgs.join('; '), a: '', r: '', tools: [], at: now, ct: r.turn, auto: false, plan: true, model: 'claude', effort, sid: session, team: true, fin: false })
  Object.assign(c, { session, engine: 'claude', model, effort, auto: false, team: true, at: now, fork: null })
  putChat(c.id, now, JSON.stringify(c))
  return run
}

let ticking = false
/** once a minute (plugins/alertwatch.ts): one run for everything that opened and was not looked at yet */
export async function tickAlertwatch() {
  if (ticking) return
  ticking = true
  try {
    const cfg = await addonSettings('alertwatch')
    if (cfg.on === false) return
    const cooldown = Math.min(168, Math.max(1, Number(cfg.cooldown) || 12)) * 3_600_000
    const now = Date.now()
    const st = await agent<{ log?: AlertEntry[] }>('/alertwatch/state')
    const last = load().lastByKey
    // a closed alert recovered on its own: never investigated
    const fresh = (st.log ?? []).filter(e => e && e.closed == null && e.at * 1000 >= now - WINDOW && !(last[e.key] > now - cooldown))
    if (fresh.length) await investigateAlerts(fresh)
  } catch (e: any) {
    console.warn(`[alertwatch] tick: ${e?.message}`)
  } finally { ticking = false }
}

/** what the page and the Home card show */
export async function alertwatchView() {
  const s = load()
  const cfg = await addonSettings('alertwatch')
  const st = await agent<{ checked: number | null, log: AlertEntry[] }>('/alertwatch/state')
  const log = Array.isArray(st.log) ? st.log : []
  const latest = (key: string) => [...s.runs].reverse().find(r => r.keys.includes(key))
  const ids = [...new Set(log.map(e => latest(e.key)?.turn).filter(Boolean))] as string[]
  const res = ids.length ? await agent<Record<string, { done: boolean, cause: string | null, allok?: boolean }>>('/alertwatch/turns', { query: { ids: ids.join(',') } }).catch(() => ({})) as Record<string, any> : {}
  const chat = s.chat ? chatById(s.chat) : null
  const withRun = (e: AlertEntry) => {
    const run = latest(e.key)
    if (!run) return { ...e, run: null }
    const r = res[run.turn] ?? {}
    const executed = !!(chat as any)?.turns?.find((t: any) => t.ct === run.turn)?.executed
    return { ...e, run: { turn: run.turn, at: run.at, done: !!r.done, cause: r.cause ?? null, allok: !!r.allok, executed } }
  }
  const newest = [...log].reverse()
  const open = log.filter(e => e.closed == null).reverse().map(withRun)
  const closedAt = log.map(e => e.closed ?? 0).reduce((a, b) => Math.max(a, b), 0)
  return {
    checked: st.checked ?? null,
    open,
    log: newest.slice(0, 20).map(withRun),
    last: newest[0] ? withRun(newest[0]) : null,
    quietSince: open.length || !log.length ? null : closedAt || null,
    chat: s.chat || null,
    on: cfg.on !== false,
  }
}
