import { existsSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import { randomUUID } from 'node:crypto'
import { join } from 'node:path'

/**
 * Scheduled chat tasks: a prompt Claude runs on its own (every day at 08:00, Mondays, every 6 h …). Each task has
 * its own chat; every run is a new turn there in a fresh session, so the chat reads like a log and a follow-up
 * question continues the latest run. `quiet` = only push when something needs the owner (the answer doesn't
 * start with ALL-OK, agent/claude.py claude_watch). Kept in one JSON file next to chats.db.
 */
export interface ChatTask {
  id: string, title: string, prompt: string
  /** "HH:MM" on `days` (0 = Sunday; empty = every day), unless `every` (hours) is set */
  time: string, days: number[], every?: number
  model: string, effort: string, auto: boolean, team: boolean, quiet: boolean, on: boolean
  chat: string, last?: number, next?: number, error?: string
}

export const TASKS_FOLDER = '⏰ Tasks'
const FILE = join(process.env.NOTES_DIR || '/var/lib/dash', 'chat-tasks.json')
const MODELS = ['fable', 'opus', 'sonnet', 'haiku'], EFFORTS = ['low', 'medium', 'high', 'xhigh', 'max']
const QUIET = '\n\n(This is a scheduled task nobody is watching live. If everything is fine and the owner needs to do nothing, answer with one line that starts with ALL-OK followed by a one-sentence summary. Otherwise explain briefly what needs attention. Do not use emoji or decorative symbols.)'

export function loadTasks(): ChatTask[] {
  try { return existsSync(FILE) ? JSON.parse(readFileSync(FILE, 'utf8')) : [] } catch { return [] }
}
function saveTasks(list: ChatTask[]) {
  writeFileSync(FILE + '.tmp', JSON.stringify(list, null, 1))
  renameSync(FILE + '.tmp', FILE)
}

/** the next time it is due after `from` */
export function nextRun(t: ChatTask, from = Date.now()) {
  if (t.every && t.every > 0) {
    const step = t.every * 3_600_000
    return t.last ? Math.max(from, t.last + step) : Math.ceil(from / 3_600_000) * 3_600_000
  }
  const [h, m] = (/^(\d{1,2}):(\d{2})$/.exec(t.time) ?? [, '8', '0']).slice(1).map(Number)
  const d = new Date(from)
  d.setHours(h!, m!, 0, 0)
  for (let i = 0; i < 8; i++, d.setDate(d.getDate() + 1)) {
    if (d.getTime() > from && (!t.days.length || t.days.includes(d.getDay()))) return d.getTime()
  }
  return from + 86_400_000
}

/** checked and normalised before it is stored */
export function putTask(raw: any) {
  const list = loadTasks()
  const old = list.find(x => x.id === raw?.id)
  const prompt = String(raw?.prompt ?? '').trim()
  if (!prompt || prompt.length > 20_000) throw createError({ statusCode: 400, statusMessage: 'the prompt is empty or too long' })
  const t: ChatTask = {
    id: old?.id ?? 't' + Math.random().toString(36).slice(2, 9),
    title: String(raw?.title ?? '').trim().slice(0, 60) || prompt.slice(0, 40),
    prompt,
    time: /^\d{1,2}:\d{2}$/.test(raw?.time) ? raw.time : '08:00',
    days: Array.isArray(raw?.days) ? [...new Set(raw.days.map(Number).filter((d: number) => d >= 0 && d <= 6))] as number[] : [],
    every: Math.min(168, Math.max(0, Math.round(Number(raw?.every) || 0))) || undefined,
    model: MODELS.includes(raw?.model) ? raw.model : 'sonnet',
    effort: EFFORTS.includes(raw?.effort) ? raw.effort : 'medium',
    auto: raw?.auto === true, team: raw?.team !== false, quiet: raw?.quiet !== false, on: raw?.on !== false,
    chat: old?.chat ?? 'k' + Math.random().toString(36).slice(2, 9),
    last: old?.last,
  }
  t.next = nextRun(t)
  saveTasks([...list.filter(x => x.id !== t.id), t])
  return t
}

export function dropTask(id: string) { saveTasks(loadTasks().filter(x => x.id !== id)) }

/** start one run: a Claude turn on pve + a new turn in the task's chat (the open pages attach to it) */
export async function runTask(id: string) {
  const list = loadTasks()
  const t = list.find(x => x.id === id)
  if (!t) throw createError({ statusCode: 404, statusMessage: 'no such task' })
  const { agentUrl, agentToken } = useRuntimeConfig()
  const session = randomUUID()
  t.last = Date.now()
  t.next = nextRun(t)
  try {
    const r = await upstream<{ turn?: string, running?: string }>('agent', agentUrl, agentToken, '/claude/send', 30_000, {
      method: 'POST', body: { chat: t.chat, session, prompt: t.prompt + (t.quiet ? QUIET : ''), auto: t.auto, model: t.model, effort: t.effort, team: t.team, quiet: t.quiet },
    })
    if (!r.turn) throw new Error('the last run is still going')
    const chat = chatById(t.chat) ?? { id: t.chat, title: t.title, at: 0, turns: [] }
    chat.task = t.id
    if (!chat.folder) chat.folder = TASKS_FOLDER
    chat.turns.push({ q: t.prompt, a: '', r: '', tools: [], at: Date.now(), ct: r.turn, auto: t.auto, model: 'claude', effort: t.effort, sid: session, team: t.team, fin: false })
    Object.assign(chat, { session, engine: 'claude', model: t.model, effort: t.effort, auto: t.auto, team: t.team, at: Date.now(), fork: null })
    putChat(chat.id, Date.now(), JSON.stringify(chat))
    t.error = undefined
  } catch (e: any) {
    t.error = String(e?.statusMessage || e?.message || e).slice(0, 200)
  }
  saveTasks(list)
  return t
}

/** once a minute (plugins/chat-tasks.ts): run what is due */
export async function tickTasks() {
  const now = Date.now()
  for (const t of loadTasks()) {
    if (t.on && (t.next ?? nextRun(t)) <= now) await runTask(t.id).catch(() => {})
  }
}
