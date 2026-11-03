import type { Chat } from '~/composables/useChats'
import { addSources, sinceClear, type Turn } from '~/composables/useAsk'

const base = (p = '') => p.split('/').filter(Boolean).pop() ?? p
const short = (s = '', n = 70) => (s = s.replace(/\s+/g, ' ').trim()).length > n ? s.slice(0, n - 1) + '…' : s

/** one pill per tool call, readable on a phone */
function label(name: string, a: any = {}) {
  switch (name) {
    case 'Bash': return `$ ${short(a.command)}`
    case 'Read': return `read ${base(a.file_path)}`
    case 'Write': return `wrote ${base(a.file_path)}`
    case 'Edit': case 'MultiEdit': return `edited ${base(a.file_path)}`
    case 'Grep': return `grep “${short(a.pattern, 40)}”`
    case 'Glob': return `files ${short(a.pattern, 40)}`
    case 'WebSearch': return `searched “${short(a.query, 50)}”`
    case 'WebFetch': return `read ${short(String(a.url ?? '').replace(/^https?:\/\//, ''), 40)}`
    case 'Task': case 'Agent': return `${a.subagent_type || 'agent'}: ${short(a.description, 50)}`
    case 'TodoWrite': return 'updated its todo list'
    default: return name
  }
}

export const CLAUDE_MODELS = [
  { id: 'auto', label: 'Auto' }, { id: 'fable', label: 'Fable 5.1' }, { id: 'opus', label: 'Opus 5.5' },
  { id: 'sonnet', label: 'Sonnet 5.5' }, { id: 'haiku', label: 'Haiku 5.5' },
]
export const CLAUDE_EFFORTS = ['auto', 'low', 'medium', 'high', 'xhigh', 'max']

const attached = new Set<string>()
const sleep = (ms: number) => new Promise(r => setTimeout(r, ms))

/**
 * Claude Code on pve, one `claude -p` per message, resumed by the chat's session id. The turn runs in its own
 * systemd unit on the host, so this side only tails its stream-json; a dropped stream (deploy, phone asleep,
 * reload) is replayed from line 0, which makes reconnecting idempotent.
 */
export function useClaude(save: () => void) {
  let saveTimer: any = null
  const saveSoon = () => { saveTimer ??= setTimeout(() => { saveTimer = null; save() }, 800) }

  const { seen } = useClaudeUsage()

  // tool start times and finished-tool durations (ms) per turn, for the ETA
  const started = new Map<string, number>(), durations = new WeakMap<Turn, number[]>()

  function apply(t: Turn, ev: any) {
    if (ev.type === 'rate_limit_event') return seen(ev.rate_limit_info)
    t.last = Date.now()
    if (ev.parent_tool_use_id) return // a subagent's inner steps — its call already shows as one pill
    if (ev.type === 'system' && ev.subtype === 'init') t.model = ev.model
    else if (ev.type === 'system' && ev.subtype === 'task_started' && ev.task_id) {
      // a background shell or task: the turn stays open until it ends, so show it
      ;(t.bg ??= []).push({ id: ev.task_id, desc: ev.description || ev.task_id, kind: ev.task_type, status: 'running', tuid: ev.tool_use_id, out: undefined })
    } else if (ev.type === 'system' && (ev.subtype === 'task_updated' || ev.subtype === 'task_notification')) {
      const b = t.bg?.find(x => x.id === ev.task_id)
      if (b) {
        const st = ev.patch?.status ?? ev.status
        if (st) b.status = st
        if (ev.output_file) b.out = ev.output_file
      }
    } else if (ev.type === 'system' && ev.subtype === 'compact_boundary') {
      // /compact, or Claude Code compacting by itself mid-answer: older messages became a summary
      const m = ev.compact_metadata ?? {}
      t.compacted = { pre: m.pre_tokens ?? 0, post: m.post_tokens ?? 0 }
      t.ctx = { ...t.ctx, used: m.post_tokens ?? 0 }
    } else if (ev.type === 'stream_event') {
      const e = ev.event
      if (e?.type === 'content_block_start' && e.content_block?.type === 'text' && t.a && !t.a.endsWith('\n\n')) t.a += '\n\n'
      if (e?.type === 'content_block_delta') {
        if (e.delta?.type === 'text_delta') t.a += e.delta.text
        else if (e.delta?.type === 'thinking_delta') t.r += e.delta.thinking
      }
    } else if (ev.type === 'assistant') {
      // the newest answer's id (an edit or branch forks the session there) and what the context held for it
      if (ev.uuid) t.uuid = ev.uuid
      const u = ev.message?.usage
      if (u) t.ctx = { ...t.ctx, used: (u.input_tokens ?? 0) + (u.cache_read_input_tokens ?? 0) + (u.cache_creation_input_tokens ?? 0) + (u.output_tokens ?? 0) }
      for (const b of ev.message?.content ?? []) {
        if (b.type === 'tool_use' && !t.tools!.some(x => x.id === b.id)) {
          t.tools!.push({ id: b.id, name: b.name, args: b.input, label: label(b.name, b.input) })
          started.set(b.id, Date.now())
        }
        if (b.type === 'tool_use' && b.name === 'TodoWrite' && Array.isArray(b.input?.todos)) {
          const todos = b.input.todos, done = todos.filter((x: any) => x?.status === 'completed').length
          const d = durations.get(t) ?? [], left = todos.length - done
          t.progress = { done, total: todos.length, etaSeconds: todos.length && left > 0 && d.length >= 2 ? Math.round(left * d.reduce((a, c) => a + c, 0) / d.length / 1000) : null }
        }
      }
    } else if (ev.type === 'user') {
      for (const b of ev.message?.content ?? []) {
        if (b.type !== 'tool_result') continue
        const tl = t.tools!.find(x => x.id === b.tool_use_id)
        if (!tl) continue
        tl.done = true
        const bgOut = /written to: (\S+\.output)/.exec(typeof b.content === 'string' ? b.content : '')?.[1]
        const bg = t.bg?.find(x => x.tuid === b.tool_use_id)
        if (bg && bgOut) bg.out = bgOut
        const t0 = started.get(b.tool_use_id)
        if (t0) { started.delete(b.tool_use_id); durations.set(t, [...(durations.get(t) ?? []), Date.now() - t0]) }
        if (!b.is_error) {
          // WebSearch result text ends in `Links: [{"title":…,"url":…},…]`; WebFetch's source is the url it was given
          if (tl.name === 'WebSearch') {
            const txt = typeof b.content === 'string' ? b.content : (b.content ?? []).map((c: any) => c.text ?? '').join('\n')
            const m = /^Links: (\[.*\])\s*$/m.exec(txt)
            if (m) { try { addSources(t, JSON.parse(m[1]!)) } catch {} }
          } else if (tl.name === 'WebFetch' && typeof tl.args?.url === 'string') {
            addSources(t, [{ title: (() => { try { return new URL(tl.args.url).hostname.replace(/^www\./, '') } catch { return '' } })(), url: tl.args.url }])
          }
        }
        if (b.is_error) {
          const msg = typeof b.content === 'string' ? b.content : (b.content ?? []).map((c: any) => c.text ?? '').join(' ')
          tl.error = /denied|don't ask mode|disabled for this session/i.test(msg) ? 'blocked' : short(msg.replace(/<\/?tool_use_error>/g, ''), 80)
        }
      }
    } else if (ev.type === 'result') {
      // a resumed session first reports background agents the last turn left behind, with an empty result of its own
      // (later in a turn, a background subagent finishing wakes the lead again: keep its totals, it's the same answer)
      if (ev.origin?.kind === 'task-notification' && !t.fin) return
      t.secs = Math.round((ev.duration_ms ?? 0) / 1000)
      const max = Math.max(0, ...Object.values(ev.modelUsage ?? {}).map((m: any) => m?.contextWindow ?? 0))
      // tokens per model (lead + subagents): what team mode moved to the cheaper ones
      t.usage = Object.fromEntries(Object.entries(ev.modelUsage ?? {}).map(([k, m]: [string, any]) => [
        k.replace(/^claude-/, '').replace(/-\d[\d-]*$/, ''),
        { tok: (m.inputTokens ?? 0) + (m.outputTokens ?? 0) + (m.cacheReadInputTokens ?? 0) + (m.cacheCreationInputTokens ?? 0), usd: m.costUSD ?? 0 },
      ]))
      if (max && t.ctx) t.ctx = { ...t.ctx, max }
      t.denied = (ev.permission_denials ?? []).map((d: any) => label(d.tool_name, d.tool_input))
      if (ev.is_error || ev.subtype !== 'success') t.error = short(String(ev.result || ev.subtype || 'failed'), 300)
      t.fin = true
    }
  }

  async function read(t: Turn, body: ReadableStream<Uint8Array>) {
    const reader = body.getReader(), dec = new TextDecoder()
    let buf = ''
    for (;;) {
      const { done, value } = await reader.read()
      if (done) return false
      buf += dec.decode(value, { stream: true })
      let i
      while ((i = buf.indexOf('\n\n')) >= 0) {
        const block = buf.slice(0, i)
        buf = buf.slice(i + 2)
        const ev = /^event: (.*)$/m.exec(block)?.[1]
        const data = block.split('\n').filter(l => l.startsWith('data: ')).map(l => l.slice(6)).join('\n')
        if (ev === 'end') {
          const err = (() => { try { return JSON.parse(data).err } catch { return '' } })()
          if (!t.fin && !t.error) t.error = t.stopped ? 'stopped' : (short(err, 300) || 'Claude exited without an answer')
          return true
        }
        if (data) { try { apply(t, JSON.parse(data)) } catch {} }
      }
      saveSoon()
    }
  }

  /** follow a running (or finished) turn until its process is gone; safe to call twice */
  async function attach(t: Turn) {
    if (!t.ct || attached.has(t.ct)) return
    attached.add(t.ct)
    t.busy = true
    try {
      for (let attempt = 0; ; attempt++) {
        Object.assign(t, { a: '', r: '', tools: [], denied: [], error: undefined, fin: false, compacted: undefined, progress: undefined, bg: undefined, sources: undefined, last: Date.now() })
        try {
          const res = await fetch(`/api/claude/stream?turn=${encodeURIComponent(t.ct)}`)
          if (res.status === 410 || res.status === 400) { t.error = 'this answer is no longer on the server'; break }
          if (res.ok && res.body && await read(t, res.body)) break
        } catch {}
        if (attempt >= 150) { t.error = 'lost the connection to the server'; break } // ~5 min: a deploy takes ~2
        await sleep(2000)
      }
    } finally {
      t.busy = false
      t.fin = true
      attached.delete(t.ct)
      save()
    }
  }

  /** opts.plan: read-only, answer with a plan + Execute button · opts.auto: write access for this one message */
  async function ask(c: Chat, text: string, imgs: string[] = [], opts: { plan?: boolean, auto?: boolean } = {}) {
    text = text.trim()
    if ((!text && !imgs.length) || c.turns.some(t => t.busy)) return
    let prompt = text || 'Here is a screenshot.'
    if (!c.session) {
      // switching an existing local-model chat over to Claude: hand it what was said so far
      const prior = sinceClear(c.turns).filter(t => !t.error).map(t => `Owner: ${t.q}\nAssistant (${t.model || 'local model'}): ${t.a}`).join('\n\n')
      if (prior) prompt = `Earlier in this chat, with a local model:\n\n${prior.slice(-12000)}\n\n---\n\n${text}`
      c.session = crypto.randomUUID()
    }
    const auto = !opts.plan && (opts.auto ?? !!c.auto)
    const team = c.team !== false
    c.turns.push({ q: text, a: '', r: '', tools: [], busy: true, at: Date.now(), auto, model: 'claude', effort: c.effort, sid: c.session, ...(opts.plan ? { plan: true } : {}), ...(team ? { team } : {}), ...(imgs.length ? { imgs } : {}) })
    const t = c.turns[c.turns.length - 1]!
    try {
      const r = await $fetch<{ turn?: string, running?: string }>('/api/claude/send', { method: 'POST', body: { chat: c.id, session: c.session, prompt, auto, model: c.model === 'auto' ? undefined : c.model, effort: c.effort === 'auto' ? undefined : c.effort, images: imgs, fork: c.fork || undefined, team, plan: !!opts.plan, ...(c.incognito ? { incognito: true } : {}) } })
      if (r.running) {
        // the last answer is still running on pve although this copy thinks it ended: follow it again
        Object.assign(t, { busy: false, fin: true, error: 'Claude is still answering the message above, send this again when it is done' })
        const live = c.turns.find(x => x.ct === r.running) ?? t
        if (live === t) Object.assign(t, { ct: r.running, error: undefined })
        live.fin = false
        save()
        return attach(live)
      }
      t.ct = r.turn
      save()
      await attach(t)
      // the copy exists now (the agent resumes a session it knows and ignores the fork point then)
      if (c.fork && t.uuid) { c.fork = null; save() }
    } catch (e: any) {
      t.error = e?.data?.statusMessage || e?.statusMessage || e?.message || 'failed'
      t.busy = false
      t.fin = true
      save()
    }
  }

  async function stop(c: Chat) {
    c.turns.forEach(t => { if (t.busy) t.stopped = true })
    await $fetch('/api/claude/stop', { method: 'POST', body: { chat: c.id } }).catch(() => {})
  }

  return { ask, attach, stop }
}
