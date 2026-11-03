<script setup lang="ts">
import { sinceClear, type Turn } from '~/composables/useAsk'
import type { Chat } from '~/composables/useChats'
import { COMMANDS, parseCommand } from '~/utils/commands'
import type { Question } from '~/utils/questions'
const { ts } = useDashConfig()
useHead({ title: 'Chat · Bastion' })
const { t: tr } = useI18n()
const { chats, current, currentId, create, remove, load, save, touch, nameChat, status } = useChats()
const claude = useClaude(save)
onMounted(load)
// a Claude turn keeps running on pve while this page is closed: pick up every one that hadn't finished, also ones
// that arrive later from another device or a scheduled task (attach ignores turns it already follows)
watch(() => chats.value.flatMap(c => c.turns.flatMap(t => [t, ...(t.cmp ?? [])])).filter(t => t.ct && !t.fin && !t.busy), (open) => {
  for (const t of open) claude.attach(t)
}, { immediate: true })

const turns = computed<Turn[]>({ get: () => current.value?.turns ?? [], set: v => (current.value!.turns = v) })
const { ask, run, stop: stopLocal, models, model: localModel } = useAsk('chat', turns as any, touch, () => !!current.value?.incognito)

// which engine a new chat starts with is remembered; each chat keeps its own afterwards
const lastEngine = () => { try { return localStorage.getItem('chat.engine') === 'claude' ? 'claude' : 'local' } catch { return 'local' } }
const engine = computed<'local' | 'claude'>({
  get: () => current.value?.engine ?? lastEngine(),
  set: (v) => {
    if (current.value) current.value.engine = v
    try { localStorage.setItem('chat.engine', v) } catch {}
    save()
  },
})
const isClaude = computed(() => engine.value === 'claude')
// model + effort: each chat keeps its own, a new chat starts with the last ones picked
const pref = (k: string, d: string) => { try { return localStorage.getItem(k) || d } catch { return d } }
function chatSetting(field: 'model' | 'effort', key: string, d: string) {
  return computed({
    get: () => current.value?.[field] ?? pref(key, d),
    set: (v: string) => {
      if (current.value) current.value[field] = v
      try { localStorage.setItem(key, v) } catch {}
      save()
    },
  })
}
const ccModel = chatSetting('model', 'chat.claude.model', 'auto')
const ccEffort = chatSetting('effort', 'chat.claude.effort', 'auto')
const auto = computed({ get: () => !!current.value?.auto, set: (v) => { if (current.value) current.value.auto = v; save() } })
const busy = computed(() => turns.value.some(t => t.busy))
const stop = () => (isClaude.value && current.value ? claude.stop(current.value) : stopLocal())
function drop(id: string) {
  const c = chats.value.find(x => x.id === id)
  if (c?.turns.some(t => t.busy && t.ct)) claude.stop(c)
  remove(id)
}

const body = ref<HTMLElement>()
const away = ref(false) // scrolled up: offer a jump back to the newest message
const onScroll = () => { const el = body.value; away.value = !!el && el.scrollHeight - el.scrollTop - el.clientHeight > 300 }
const toBottom = (smooth = true) => body.value?.scrollTo({ top: body.value.scrollHeight, behavior: smooth ? 'smooth' : 'auto' })
watch(() => turns.value.map(t => t.a.length + t.r.length + (t.tools?.length ?? 0)).join(), () => {
  const el = body.value
  if (el && el.scrollHeight - el.scrollTop - el.clientHeight < 200) nextTick(() => (el.scrollTop = el.scrollHeight))
  nextTick(onScroll)
})
watch(currentId, () => nextTick(() => { toBottom(false); onScroll() }))
// phone keyboard: 100dvh ignores it, so the input could end up behind it. While it is up the chat
// fills the visible part of the screen (visualViewport) and the tab bar steps aside
// Chrome on Android only shrinks the visual viewport, Samsung Internet/Firefox may shrink the whole page,
// so "keyboard up" = clearly shorter than the tallest it has been at this width
let tallest = 0, wide = 0
function onViewport() {
  const vv = window.visualViewport
  if (!vv || window.innerWidth > 640) return
  if (window.innerWidth !== wide) { wide = window.innerWidth; tallest = 0 } // rotated
  tallest = Math.max(tallest, vv.height, window.innerHeight)
  const kb = tallest - vv.height > 150
  const root = document.documentElement
  const was = root.classList.contains('kb')
  root.classList.toggle('kb', kb)
  root.style.setProperty('--vvh', `${Math.round(vv.height)}px`)
  if (kb) window.scrollTo(0, 0)
  if (kb !== was && !away.value) nextTick(() => toBottom(false))
}
onMounted(() => { onViewport(); window.visualViewport?.addEventListener('resize', onViewport); window.visualViewport?.addEventListener('scroll', onViewport) })
onBeforeUnmount(() => {
  window.visualViewport?.removeEventListener('resize', onViewport)
  window.visualViewport?.removeEventListener('scroll', onViewport)
  document.documentElement.classList.remove('kb')
})
// opening the page lands on the newest message; again once markdown/images have laid out
onMounted(() => nextTick(() => { toBottom(false); setTimeout(() => { toBottom(false); onScroll() }, 150) }))

/** ask the last question again: replaces a failed or stopped answer, or rolls the dice again on a local model */
const canRetry = computed(() => !busy.value && !!turns.value.at(-1)?.q && (!isClaude.value || !!turns.value.at(-1)!.error))
function retry() {
  const c = current.value
  if (!c || !canRetry.value) return
  const { q, imgs } = c.turns.pop()!
  save()
  send(q, imgs)
}
const STATUS = { busy: 'working…', input: 'needs your answer' } as const

// a short line above the input confirming what a command did
const flash = ref('')
let flashT: any
function say(s: string) { flash.value = s; clearTimeout(flashT); flashT = setTimeout(() => (flash.value = ''), 3000) }

// --- memory: /remember, /forget, the panel, and "Remember this?" suggestions after an answer ------------------
const mem = useMemory()
const memOpen = ref(false)
onMounted(mem.load)
async function remember(text: string, src = current.value?.id) {
  try { const r = await mem.add(text, src); say(r.dup ? tr('memory.already') : tr('memory.remembered')) } catch (e: any) { say(e?.data?.statusMessage || 'could not save') }
}
async function forget(text: string) {
  const n = text.trim().toLowerCase()
  const hits = mem.facts.value.filter(f => f.text.toLowerCase().includes(n))
  if (!n || !hits.length) return say(tr('memory.none', { text }))
  if (hits.length > 1) return say(tr('memory.several', { n: hits.length, list: hits.slice(0, 3).map(f => `“${f.text.slice(0, 40)}”`).join(', ') }))
  await mem.del(hits[0]!.id).catch(() => {})
  say(tr('memory.forgot', { text: hits[0]!.text.slice(0, 60) }))
}
function memRemember(i: number, f: string) { const t = turns.value[i]; if (t) t.mem = (t.mem ?? []).filter(x => x !== f); remember(f); touch() }
function memSkip(i: number, f: string) { const t = turns.value[i]; if (t) t.mem = (t.mem ?? []).filter(x => x !== f); touch() }
// once per finished answer of at least 200 characters; never in incognito, silent when the model is unavailable
const memTried = new WeakSet<Turn>()
watch(() => turns.value.map(t => !!t.busy).join(), () => {
  const c = current.value, t = turns.value[turns.value.length - 1]
  if (!c || c.incognito || !t || t.busy || t.error || t.clear || t.cmp || memTried.has(t) || t.mem || t.a.length < 200 || Date.now() - (t.at ?? 0) > 3_600_000) return
  memTried.add(t)
  mem.suggest(t.q, t.a).then((fs) => { if (fs.length) { t.mem = fs; touch() } })
})

// note titles for /note, fetched once
const noteTitles = ref<string[]>([])
onMounted(() => $fetch<any>('/api/notes').then(r => (noteTitles.value = (r.notes ?? []).filter((n: any) => n.state === 'active').map((n: any) => n.title))).catch(() => {}))
const commands = computed(() => COMMANDS.filter(c => isClaude.value || !c.claude).map(c => ({
  ...c,
  choices: c.name === 'model' ? (isClaude.value ? CLAUDE_MODELS.map(m => m.id) : models.value.map((m: any) => m.name))
    : c.name === 'effort' ? CLAUDE_EFFORTS : c.name === 'note' ? noteTitles.value : undefined,
})))

/** our slash commands; false = not one of them, so it goes to the model as typed (Claude's own skills) */
function command(text: string): boolean {
  const p = parseCommand(text)
  if (!p?.cmd) return false
  const { cmd, arg } = p
  if (cmd.claude && !isClaude.value) return say(`/${cmd.name} needs Claude`), true
  if (busy.value && !cmd.busy) return say('wait until the answer is done (or /stop)'), true
  switch (cmd.name) {
    case 'clear': clear(); return true
    case 'new': create(); return true
    case 'team': team.value = !team.value; say(team.value ? tr('chat.teamOn') : tr('chat.teamOff')); return true
    case 'tasks': tasksOpen.value = true; return true
    case 'remember': arg.trim() ? remember(arg) : say(tr('memory.needText')); return true
    case 'forget': arg.trim() ? forget(arg) : say(tr('memory.none', { text: '' })); return true
    case 'export': exportMd(); return true
    case 'plan': if (!isClaude.value) return say(tr('chat.needsClaude')), true
      deliver(arg, [], { plan: true }); return true
    case 'compare': if (current.value) cmp.compare(current.value, arg).then(touch); return true
    case 'stop': if (busy.value) stop(); return true
    case 'retry': canRetry.value ? retry() : say(isClaude.value ? 'only a failed or stopped answer can be retried' : 'nothing to retry'); return true
    case 'auto': case 'readonly':
      auto.value = cmd.name === 'auto'
      say(auto.value ? 'Auto: Claude may change things' : 'Read-only: Claude can only look')
      return true
    case 'effort':
      if (!CLAUDE_EFFORTS.includes(arg.toLowerCase())) return say(`effort is one of ${CLAUDE_EFFORTS.join(', ')}`), true
      ccEffort.value = arg.toLowerCase(); say(`effort → ${ccEffort.value}`); return true
    case 'model': {
      const a = arg.toLowerCase()
      if (isClaude.value) {
        const m = CLAUDE_MODELS.find(m => m.id === a) ?? CLAUDE_MODELS.find(m => m.label.toLowerCase().startsWith(a))
        if (!m) return say(`model is one of ${CLAUDE_MODELS.map(m => m.id).join(', ')}`), true
        ccModel.value = m.id; say(`model → ${m.label}`); return true
      }
      const m = models.value.find((m: any) => m.name === a) ?? models.value.find((m: any) => m.name.toLowerCase().includes(a))
      if (!m) return say(`no local model “${arg}”`), true
      localModel.value = m.name; say(`model → ${m.name}`); return true
    }
  }
  if (cmd.prompt) { deliver(cmd.prompt(arg)); return true }
  return false
}
function send(q: string, imgs: string[] = []) {
  if (!imgs.length && q.trim().startsWith('/') && command(q)) return
  if (busy.value && current.value) return enqueue(current.value.id, q, imgs)
  deliver(q, imgs)
}

// handle for the voice add-on (hands-free loop): it sends and reads answers through this, never imports the page
const { list: addonList, isOn } = useAddons()
const voiceOn = computed(() => addonList.some(a => a.id === 'voice') && isOn('voice'))
const voiceRunning = computed(() => useState('voice:state').value !== 'off')
const voiceHandle = useState<any>('chat:voice', () => null)
const speaker = useSpeak()
// read-aloud on an answer: with the voice add-on it starts the hands-free loop (read it, then listen); tap again = stop
function readAloud(key: string, text: string, full: boolean) {
  if (!voiceOn.value) return speaker.speak(key, text, full)
  const v = useVoiceLoop()
  if (v.on.value && speaker.speaking.value === key) return v.stop()
  if (v.on.value) v.stop()
  v.start({ key, text, full })
}
onMounted(() => {
  voiceHandle.value = {
    send: (text: string) => send(text),
    engineLabel: () => (isClaude.value ? 'Claude' : 'local model'),
    lastAnswer: () => {
      const t = turns.value[turns.value.length - 1]
      return { text: t?.a ?? '', busy: !!t?.busy, n: turns.value.length, error: t?.error ? String(t.error) : undefined }
    },
    idle: () => !busy.value,
  }
})
onBeforeUnmount(() => { voiceHandle.value = null })

// --- queue (idea from Odysseus): messages typed while an answer runs wait here and go out together when it is
// done. Kept on this device only (two devices draining one queue would send it twice). A stopped or failed answer
// holds the queue until "Send now".
interface Queued { text: string, imgs: string[] }
const QKEY = 'chat.queue'
const queues = ref<Record<string, Queued[]>>({})
const held = ref<Record<string, boolean>>({})
const promote = new Set<string>() // "Send now" while busy: stop the answer, then send even though it was stopped
onMounted(() => { try { queues.value = JSON.parse(localStorage.getItem(QKEY) || '{}') || {} } catch {} })
watch(queues, v => { try { localStorage.setItem(QKEY, JSON.stringify(Object.fromEntries(Object.entries(v).filter(([, q]) => q.length)))) } catch {} }, { deep: true })
const queue = computed(() => queues.value[currentId.value] ?? [])
function enqueue(id: string, text: string, imgs: string[] = [], first = false) {
  const q = queues.value[id] ??= []
  first ? q.unshift({ text, imgs }) : q.push({ text, imgs })
}
const unqueue = (i: number) => queues.value[currentId.value]?.splice(i, 1)
function drain(c: Chat) {
  const qs = queues.value[c.id]
  if (!qs?.length || c.turns.some(t => t.busy)) return
  const claudeChat = c.engine === 'claude' || (c.id === currentId.value && isClaude.value)
  if (!claudeChat && c.id !== currentId.value) return // the local model only answers the chat on screen
  const items = qs.splice(0)
  const text = items.map(m => m.text).filter(Boolean).join('\n\n'), imgs = items.flatMap(m => m.imgs)
  held.value[c.id] = false
  if (c.id === currentId.value) return deliver(text, imgs)
  Object.assign(c, { engine: 'claude', model: c.model ?? ccModel.value, effort: c.effort ?? ccEffort.value })
  claude.ask(c, text, imgs)
}
// a Claude answer finished: name the chat (nameChat skips anything that is busy, named or incognito)
watch(() => chats.value.map(c => `${c.id}:${c.turns.some(t => t.busy)}`).join(), (now, prev) => {
  const was = new Set((prev ?? '').split(',').filter(x => x.endsWith(':true')).map(x => x.slice(0, -5)))
  for (const c of chats.value) if (was.has(c.id) && !c.turns.some(t => t.busy)) nameChat(c).catch(() => {})
})
// an answer ended somewhere: send what was queued for that chat
watch(() => chats.value.map(c => `${c.id}:${c.turns.some(t => t.busy)}`).join(), () => {
  for (const c of chats.value) {
    if (!queues.value[c.id]?.length || c.turns.some(t => t.busy) || held.value[c.id]) continue
    const last = c.turns.at(-1)
    if ((last?.stopped || last?.error) && !promote.has(c.id)) { held.value[c.id] = true; continue }
    promote.delete(c.id)
    drain(c)
  }
})
function sendNow() {
  const c = current.value
  if (!c) return
  if (busy.value) { promote.add(c.id); held.value[c.id] = false; stop() } else drain(c)
}
// the stall banner's nudge: stop the silent answer and tell Claude to carry on
function nudge() {
  const c = current.value
  if (!c) return
  enqueue(c.id, 'You went quiet for a while. If a command hangs, give up on it and try another way; otherwise continue where you left off.', [], true)
  sendNow()
}

// --- edit / branch (idea from Odysseus). Claude: the new session is a copy of the old one up to the answer
// before the edited question (claude --resume-session-at --fork-session); messages before a compaction are gone
// from Claude's copy, so the fork point has to come after the last one.
const bar = ref<{ setText: (v: string) => void }>()
function forkable(c: Chat | undefined, i: number) {
  const t = c?.turns[i]
  if (!c || !t || t.busy || t.clear) return false
  if (c.engine !== 'claude') return !!t.q && !t.ct
  return !!(t.uuid && t.sid) && !c.turns.slice(i + 1).some(x => x.sid === t.sid && x.compacted)
}
const canFork = (i: number) => !busy.value && forkable(current.value, i)
function canEdit(i: number) {
  const c = current.value, t = c?.turns[i]
  if (!c || !t?.q || busy.value || t.q === '/compact') return false
  if (c.engine !== 'claude') return !t.ct
  const prev = c.turns[i - 1]
  return !prev || !!prev.clear || forkable(c, i - 1)
}
const { arm: armEdit } = useArm()
const { toast } = useToast()
function edit(i: number) {
  const c = current.value
  if (!c || !canEdit(i)) return
  const t = c.turns[i]!, prev = c.turns[i - 1]
  if (i < c.turns.length - 1 && !armEdit(`${c.id}:${i}`)) return toast(tr('chat.editConfirm', { n: c.turns.length - i - 1 }), { tone: 'warn' })
  if (c.engine === 'claude') {
    c.session = crypto.randomUUID()
    c.fork = prev && !prev.clear ? { from: prev.sid!, at: prev.uuid! } : null
  }
  c.turns = c.turns.slice(0, i)
  save()
  bar.value?.setText(t.q)
}
function fork(i: number) {
  const src = current.value
  if (!src || !canFork(i)) return
  const t = src.turns[i]!
  const turns: Turn[] = JSON.parse(JSON.stringify(src.turns.slice(0, i + 1))).map((x: Turn) => ({ ...x, busy: false, fin: true }))
  const c = create()
  Object.assign(c, { title: tr('chat.branchTitle', { title: src.title }), engine: src.engine, model: src.model, effort: src.effort, turns })
  if (src.engine === 'claude') Object.assign(c, { session: crypto.randomUUID(), fork: { from: t.sid!, at: t.uuid! } })
  save()
  say(tr('chat.branched'))
}

// --- context ring: how full Claude's context is after the last answer, and a Compact button (idea from Odysseus)
const ctxOpen = ref(false)
const ctx = computed(() => {
  if (!isClaude.value) return null
  const ts = sinceClear(turns.value)
  const last = ts.findLast(t => t.ctx?.used)
  if (!last) return null
  const max = last.ctx!.max ?? ts.findLast(t => t.ctx?.max)?.ctx?.max ?? 200_000
  return { used: last.ctx!.used, max, pct: Math.min(100, Math.round(last.ctx!.used / max * 100)), msgs: ts.filter(t => t.q).length }
})
const kt = (n: number) => (n >= 1e6 ? `${+(n / 1e6).toFixed(1)}M` : n >= 1000 ? `${Math.round(n / 1000)}k` : String(n))
function compactNow() { ctxOpen.value = false; send('/compact') }

// --- sidebar: search, pinned on top, then by day
const find = ref('')
const hit = (c: Chat, w: string) => c.title.toLowerCase().includes(w) || c.turns.some(t => t.q?.toLowerCase().includes(w) || t.a?.toLowerCase().includes(w))
// folders: free-text names on the chat, shown as collapsible sections above the date groups
const folders = computed(() => [...new Set(chats.value.filter(c => c.folder).map(c => c.folder!))].sort((a, b) => a.localeCompare(b)))
const allFolders = computed(() => [...new Set(chats.value.map(c => c.folder).filter(Boolean) as string[])].sort((a, b) => a.localeCompare(b)))
const SHUT = 'chat.folders.shut' // which folders are closed; kept per browser
const shut = ref<Record<string, boolean>>({})
onMounted(() => { try { shut.value = JSON.parse(localStorage.getItem(SHUT) || '{}') || {} } catch {} })
watch(shut, v => { try { localStorage.setItem(SHUT, JSON.stringify(v)) } catch {} }, { deep: true })
const moveFor = ref('')
const newFolder = ref('')
function setFolder(c: Chat, name: string) {
  name = name.replace(/\s+/g, ' ').trim().slice(0, 24)
  if (name) c.folder = name
  else delete c.folder
  moveFor.value = ''; newFolder.value = ''
  save()
}
const sorting = ref(false)
const idle = (c: Chat) => !c.turns.some(t => t.busy || (t.ct && !t.fin))
// ask the local model where chats belong; best-effort, a failure leaves them where they are
async function sortChats(list: Chat[], quiet = false) {
  list = list.filter(c => !c.folder && !c.incognito && c.turns.length && idle(c))
  if (!list.length) { if (!quiet) toast(tr('chat.sortNone')); return }
  sorting.value = true
  try {
    const r = await $fetch<Record<string, string>>('/api/chats/sort', {
      method: 'POST', timeout: 300_000,
      body: { items: list.map(c => ({ id: c.id, title: c.title, q: c.turns[0]!.q.slice(0, 300) })), folders: allFolders.value },
    })
    let n = 0
    for (const c of list) {
      const f = r[c.id]
      if (f && !c.folder && idle(c)) { c.folder = f.slice(0, 24); n++ }
    }
    if (n) save()
    if (!quiet) toast(tr('chat.sorted', { n, m: list.length }))
  } catch { if (!quiet) toast(tr('chat.sortFailed'), { tone: 'warn' }) } finally { sorting.value = false }
}
const groups = computed(() => {
  const w = find.value.trim().toLowerCase()
  if (w) return [{ key: 'found', label: tr('chat.found'), list: chats.value.filter(c => hit(c, w)) }]
  const day = new Date(); day.setHours(0, 0, 0, 0)
  const t0 = day.getTime(), DAY = 86_400_000
  const live = chats.value
  const by = (lo: number, hi: number) => live.filter(c => !c.pinned && !c.folder && c.at >= lo && c.at < hi)
  const foldered = (n: string) => live.filter(c => !c.pinned && c.folder === n)
  return [
    { key: 'pinned', label: tr('chat.pinned'), list: live.filter(c => c.pinned) },
    ...folders.value.map(n => ({ key: `f:${n}`, label: n, folder: true, list: foldered(n) })),
    { key: 'today', label: tr('chat.today'), list: by(t0, Infinity) },
    { key: 'yday', label: tr('chat.yesterday'), list: by(t0 - DAY, t0) },
    { key: 'week', label: tr('chat.week'), list: by(t0 - 7 * DAY, t0 - DAY) },
    { key: 'older', label: tr('chat.older'), list: by(0, t0 - 7 * DAY) },
  ].filter(g => g.list.length)
})
function flag(c: Chat, k: 'pinned') {
  c[k] = !c[k]
  save()
}
// --- team mode, plan → execute, compare, scheduled tasks, export / note, incognito ------------------------------
// team: the chosen model leads and hands reading/editing to cheaper subagents when the task is big (agent/claude.py)
const team = computed({ get: () => current.value?.team !== false, set: (v) => { if (current.value) current.value.team = v; save() } })
const menu = ref(false)
const planNext = ref(false) // the next message is answered as a plan with an Execute button
function execute(i: number) {
  const c = current.value, t = c?.turns[i]
  if (!c || !t || busy.value) return
  t.executed = true
  claude.ask(c, 'Go ahead: carry out the plan above now. Stick to it; if something turns out different from what the plan assumed, stop and tell me.', [], { auto: true })
  nextTick(touch)
}
const cmp = useCompare(claude, save)
const tasksOpen = ref(false)
function openChat(id: string) {
  tasksOpen.value = false
  // a task's first run arrives with the next pull
  const go = () => { if (chats.value.some(c => c.id === id)) { currentId.value = id; return true } }
  if (!go()) { let n = 0; const iv = setInterval(() => { if (go() || ++n > 10) clearInterval(iv) }, 1000) }
}
const chatMd = (c: Chat) => `# ${c.title}\n\n` + c.turns.filter(t => !t.clear).map(t => {
  if (t.cmp) return `**Owner:** ${t.q}\n\n` + t.cmp.map(p => `**${p.label}:**\n\n${p.a}`).join('\n\n')
  return `**Owner:** ${t.q}\n\n**${t.model === 'claude' || t.ct ? 'Claude' : t.model || 'Assistant'}:**\n\n${t.a}`
}).join('\n\n---\n\n')
function exportMd() {
  const c = current.value
  if (!c?.turns.length) return
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(new Blob([chatMd(c)], { type: 'text/markdown' })),
    download: `${c.title.replace(/[^\w\- ]+/g, '').trim().slice(0, 50) || 'chat'}.md`,
  })
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}
async function toNote(text: string) {
  try {
    await $fetch('/api/notes/action', { method: 'POST', body: { action: 'add', text: text.slice(0, 50_000), ai: true } })
    say(tr('chat.noted'))
  } catch (e: any) { say(e?.data?.statusMessage || e?.message || 'failed') }
}
function noteTurn(i: number) {
  const c = current.value, t = c?.turns[i]
  if (c && t) toNote(`${t.a}\n\n(from the chat “${c.title}”: /chat?c=${c.id})`)
}
const noteChat = () => current.value && toNote(chatMd(current.value).slice(0, 50_000) + `\n\n(/chat?c=${current.value.id})`)
function incognito() { create(true); menu.value = false; say(tr('chat.incognitoHint')) }

const history = computed(() => turns.value.filter(t => t.q && !t.clear).map(t => t.q).filter((q, i, a) => q !== a[i - 1]))
function deliver(q: string, imgs: string[] = [], opts: { plan?: boolean, auto?: boolean } = {}) {
  if (isClaude.value && current.value) {
    Object.assign(current.value, { engine: 'claude', model: ccModel.value, effort: ccEffort.value })
    if (planNext.value) { opts = { ...opts, plan: true }; planNext.value = false }
    claude.ask(current.value, q, imgs, opts)
  } else ask(q)
  nextTick(touch)
}
// from the command palette: ?c=<id> opens that chat, ?ask=<question> asks it in a fresh one
const route = useRoute()
function fromQuery() {
  const { c, ask: q } = route.query
  if (!c && !q) return
  if (typeof c === 'string' && chats.value.some(x => x.id === c)) currentId.value = c
  if (typeof q === 'string' && q.trim() && !busy.value) { if (current.value?.turns.length) create(); nextTick(() => send(q.trim())) }
  navigateTo({ query: {} }, { replace: true })
}
onMounted(() => nextTick(fromQuery))
watch(() => route.query, fromQuery)
/** like Claude Code's /clear: the screen empties and the model starts over (Claude gets a fresh session) */
function clear() {
  const c = current.value
  if (!c || busy.value || !c.turns.length) return
  c.turns = []
  c.title = 'New chat' // the next question names it again
  if (c.session) c.session = crypto.randomUUID()
  save()
}
const EXAMPLES = {
  local: ['What can you do?', 'Summarise how my server is doing', 'Explain ZFS snapshots vs backups', 'What happened in tech news today?'],
  claude: ['Which of my notes are ideas I could build?', 'Is anything broken on the server right now?', 'Why did the last backup take so long?', 'What changed in the dashboard today?'],
}
const open = ref(false) // conversation list on phones

// open questions sit above the input, apart from the chat; typing a message instead answers them too
const pending = computed<{ t: Turn, qs: Question[] } | null>(() => {
  const t = turns.value.at(-1)
  if (!t || t.busy || t.clear || t.error || t.answered) return null
  const qs = splitQuestions(t.a).qs
  return qs ? { t, qs } : null
})
const qsMin = ref(false)
watch(() => pending.value?.t, () => (qsMin.value = false))
function answer(text: string, picked: Record<number, string[]>) {
  if (!pending.value) return
  pending.value.t.answered = picked
  send(text)
}
</script>

<template>
  <div class="chat">
    <div v-if="open" class="scrim" @click="open = false" />
    <aside :class="{ open }">
      <button class="btn primary new" @click="create(); open = false">+ New chat</button>
      <button type="button" class="lnk small sortall" :disabled="sorting" @click="sortChats(chats)"><template v-if="sorting">{{ $t('chat.sorting') }}</template><template v-else><Icon name="sparkles" :size="14"/> {{ $t('chat.sortAll') }}</template></button>
      <label class="find"><Icon name="search" :size="14" /><input v-model="find" type="search" :placeholder="$t('chat.search')"></label>
      <div class="list">
        <template v-for="g in groups" :key="g.key">
        <div class="glab small faint" :class="{ fold: (g as any).folder }" @click="(g as any).folder && (shut[g.key] = !shut[g.key])">
          <template v-if="(g as any).folder"><Icon :name="shut[g.key] ? 'chevron-right' : 'chevron-down'" :size="14"/> <Icon name="folder" :size="14" style="margin-right:6px"/></template>{{ g.label }}<template v-if="(g as any).folder"> ({{ g.list.length }})</template>
        </div>
        <template v-if="!shut[g.key]">
        <template v-for="c in g.list" :key="c.id">
        <button
          class="conv" :class="{ on: c.id === currentId }"
          @click="currentId = c.id; open = false"
        >
          <span class="t"><span v-if="c.engine === 'claude'" class="cl" title="Claude"><Icon name="spark" :size="12"/></span>{{ c.title }}</span>
          <span v-if="status(c)" class="small st" :class="status(c)"><span class="sd" />{{ STATUS[status(c) as 'busy'] }}</span>
          <span v-else class="small faint">{{ ago(c.at / 1000) }}</span>
          <span class="cacts">
            <span class="ca" :class="{ lit: c.pinned }" :title="c.pinned ? $t('chat.unpin') : $t('chat.pin')" @click.stop="flag(c, 'pinned')"><Icon name="pin" :size="13" /></span>
            <span class="ca" :class="{ lit: !!c.folder }" :title="$t('chat.moveTo')" @click.stop="moveFor = moveFor === c.id ? '' : c.id; newFolder = ''"><Icon name="folder" :size="14"/></span>
            <span class="ca x" title="delete" @click.stop="drop(c.id)"><Icon name="x" :size="14"/></span>
          </span>
        </button>
        <div v-if="moveFor === c.id" class="mover small">
          <button v-for="f in allFolders" :key="f" type="button" :class="{ on: c.folder === f }" @click="setFolder(c, f)"><Icon name="folder" :size="14"/> {{ f }}</button>
          <form class="nf" @submit.prevent="setFolder(c, newFolder)">
            <input v-model="newFolder" maxlength="24" :placeholder="$t('chat.newFolder')">
            <button type="submit" :disabled="!newFolder.trim()">+</button>
          </form>
          <button v-if="c.folder" type="button" @click="setFolder(c, '')"><Icon name="x" :size="14"/> {{ $t('chat.noFolder') }}</button>
        </div>
        </template>
        </template>
        </template>
        <div v-if="!groups.length" class="small faint glab">{{ $t('chat.noMatch') }}</div>
      </div>
      <ClaudeUsage />
      <a :href="ts('ai')" target="_blank" class="small muted webui" title="for files, images, uncensored models">Open WebUI <Icon name="external-link" :size="12"/></a>
    </aside>

    <section class="main">
      <div class="mhead">
        <button class="btn ghost only-phone" title="conversations" @click="open = !open" aria-label="conversations"><Icon name="panel-left" :size="18"/></button>
        <b class="ttl"><span v-if="current?.incognito" :title="$t('chat.incognito')"><Icon name="eye-off" :size="16"/> </span>{{ current?.title ?? 'Chat' }}</b>
        <span v-if="status(current) === 'input'" class="st input small hide-phone"><span class="sd" />your turn</span>
        <div class="seg" role="group" aria-label="engine">
          <button :class="{ on: !isClaude }" :disabled="busy" title="local model on the 3060 (Ollama)" @click="engine = 'local'"><span class="only-phone-i"><Icon name="bot" :size="16"/></span><span class="hide-phone">Local</span></button>
          <button :class="{ on: isClaude }" :disabled="busy" title="Claude Code on the host, your subscription" @click="engine = 'claude'"><span class="only-phone-i"><Icon name="spark" :size="16"/></span><span class="hide-phone">Claude</span></button>
        </div>
        <button
          v-if="isClaude" class="btn ghost autobtn" :class="{ armed: auto }" :disabled="busy"
          :title="auto ? 'Claude may change files, run commands and deploy. Click for read-only' : 'Claude can only look. Click to let it change things'"
          @click="auto = !auto"
        ><Icon :name="auto ? 'zap' : 'eye'" :size="16"/><span class="hide-phone">{{ auto ? ' Auto' : ' Read-only' }}</span></button>
        <div v-if="ctx" class="ctxw">
          <button type="button" class="btn ghost ring" :class="{ warn: ctx.pct >= 70, bad: ctx.pct >= 85 }" :title="$t('chat.context')" @click="ctxOpen = !ctxOpen">
            <svg viewBox="0 0 20 20" width="18" height="18"><circle cx="10" cy="10" r="8" class="rt" /><circle cx="10" cy="10" r="8" class="rv" :stroke-dasharray="`${ctx.pct * 0.5027} 50.27`" /></svg>
            <span class="small hide-phone">{{ ctx.pct }}%</span>
          </button>
          <div v-if="ctxOpen" class="ctxpop small">
            <div><b>{{ $t('chat.context') }}</b> <span class="muted">{{ kt(ctx.used) }} / {{ kt(ctx.max) }} · {{ ctx.pct }}%</span></div>
            <div class="cbar"><span :style="{ width: ctx.pct + '%' }" /></div>
            <div class="muted">{{ $t('chat.messages', { n: ctx.msgs }) }}</div>
            <button type="button" class="btn sm" :disabled="busy" @click="compactNow">{{ $t('chat.compact') }}</button>
          </div>
        </div>
        <button
          v-if="turns.length" class="btn ghost clearbtn hide-phone" :disabled="busy"
          title="clear this chat and start fresh (same as typing /clear)" @click="clear"
        >⟲</button>
        <div class="menuw">
          <button type="button" class="btn ghost mbtn" :class="{ on: menu }" :title="$t('chat.more')" @click="menu = !menu">⋯</button>
          <div v-if="menu" class="menu small" @click="menu = false">
            <button v-if="isClaude" type="button" @click.stop="team = !team"><Icon name="users" :size="16"/> {{ $t('chat.team') }} <span class="faint">{{ team ? $t('chat.on') : $t('chat.off') }}</span></button>
            <button v-if="isClaude" type="button" :disabled="busy" @click="planNext = true"><Icon name="file-text" :size="16"/> {{ $t('chat.planNext') }}</button>
            <button type="button" :disabled="busy" @click="say($t('chat.compareHint'))"><Icon name="scale" :size="16"/> {{ $t('chat.compareMenu') }}</button>
            <button type="button" @click="tasksOpen = true"><Icon name="alarm-clock" :size="16"/> {{ $t('chat.tasks') }}</button>
            <button type="button" @click="memOpen = true"><Icon name="brain" :size="16"/> {{ $t('memory.menu') }} <span class="faint">{{ mem.count.value }}</span></button>
            <button type="button" :disabled="!turns.length" @click="noteChat"><Icon name="note" :size="16"/> {{ $t('chat.saveNote') }}</button>
            <button type="button" :disabled="!turns.length" @click="exportMd"><Icon name="download" :size="16"/> {{ $t('chat.exportMd') }}</button>
            <button type="button" class="only-phone" @click="create()"><Icon name="plus" :size="16"/> {{ $t('chat.newChat') }}</button>
            <button type="button" @click.stop="incognito"><Icon name="eye-off" :size="16"/> {{ $t('chat.incognito') }}</button>
            <button type="button" class="only-phone" :disabled="busy || !turns.length" @click="clear">⟲ {{ $t('chat.clear') }}</button>
          </div>
        </div>
      </div>

      <div class="bodywrap">
      <div ref="body" class="body" @scroll.passive="onScroll">
        <div v-if="!turns.length" class="empty muted">
          <div class="hero" :class="engine">
            <span class="logo"><Icon :name="isClaude ? 'spark' : 'bot'" :size="16"/></span>
            <b>{{ isClaude ? 'Claude on pve' : 'Local model' }}</b>
          </div>
          <div class="examples">
            <button v-for="ex in EXAMPLES[engine]" :key="ex" class="pill" @click="send(ex)">{{ ex }}</button>
          </div>
        </div>
        <AskTurns
          v-else dock extras :turns="turns" :retry="canRetry" :can-edit="canEdit" :can-fork="canFork"
          @run="p => run(p)" @answer="send" @retry="retry" @edit="edit" @fork="fork" @stop="stop" @nudge="nudge"
          @note="noteTurn" @speak="readAloud" @execute="execute" @remember="memRemember" @skip-mem="memSkip"
        >
          <template #compare="{ turn }"><CompareTurn :turn="turn" :score="cmp.score.value" @vote="k => cmp.vote(turn, k)" /></template>
        </AskTurns>
        <div v-if="queue.length" class="queued">
          <div v-for="(m, i) in queue" :key="i" class="qq">
            <span class="small faint">{{ $t('chat.queued') }}</span>
            <div class="qb">{{ m.text }}<span v-if="m.imgs.length" class="faint"> · <Icon name="paperclip" :size="12"/> {{ m.imgs.length }}</span></div>
            <button type="button" class="ca" :title="$t('chat.unqueue')" @click="unqueue(i)" :aria-label="$t('chat.unqueue')"><Icon name="x" :size="14"/></button>
          </div>
          <button type="button" class="btn sm" @click="sendNow">{{ busy ? $t('chat.sendNowBusy') : $t('chat.sendNow') }}</button>
        </div>
      </div>
      <button v-if="away" class="jump" title="newest message" @click="toBottom()" aria-label="newest message"><Icon name="chevron-down" :size="18"/></button>
      </div>

      <div v-if="pending" class="dock" :class="{ min: qsMin }">
        <div class="dhead small">
          <span class="warn"><Icon name="circle-help" :size="14"/> {{ pending.qs.length === 1 ? 'Claude needs your answer' : `${pending.qs.length} questions for you` }}</span>
          <button type="button" class="btn ghost dmin" :title="qsMin ? 'show the questions' : 'tuck them away'" @click="qsMin = !qsMin">{{ qsMin ? 'show' : 'hide' }} <Icon :name="qsMin ? 'chevron-up' : 'chevron-down'" :size="14"/></button>
        </div>
        <AskQuestions v-show="!qsMin" :key="turns.length" :qs="pending.qs" @answer="answer" />
      </div>

      <div v-if="memOpen" class="tasks"><ChatMemory @close="memOpen = false" /></div>
      <div v-if="tasksOpen" class="tasks"><ChatTasks @close="tasksOpen = false" @open="openChat" /></div>
      <div class="bar" :class="{ armed: isClaude && auto }">
        <VoiceDock v-if="voiceOn && voiceRunning" />
        <div v-if="flash" class="flash small">{{ flash }}</div>
        <div v-if="planNext" class="flash small"><Icon name="file-text" :size="14"/> {{ $t('chat.planOn') }} <button type="button" class="lnk" @click="planNext = false">{{ $t('common.cancel') }}</button></div>
        <AskBar
          ref="bar" :history="history" voice queue
          :busy="busy" :models="isClaude ? [{ name: 'claude' }] : models" :commands="commands"
          :draft-key="current ? `chat:draft:${current.id}` : undefined" :images="isClaude"
          :placeholder="busy ? $t('chat.queuePh') : pending ? 'Or type your own answer…' : !isClaude ? 'Message the local model…' : auto ? 'Tell Claude what to change…' : 'Ask Claude (read-only)…'"
          @submit="send" @stop="stop"
        >
          <template v-if="isClaude" #opts>
            <select v-model="ccModel" title="Claude model" :disabled="busy">
              <option v-for="m in CLAUDE_MODELS" :key="m.id" :value="m.id">{{ m.label }}</option>
            </select>
            <select v-model="ccEffort" title="effort: how long Claude thinks before and while answering" :disabled="busy">
              <option v-for="e in CLAUDE_EFFORTS" :key="e" :value="e">{{ e }} effort</option>
            </select>
          </template>
        </AskBar>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* fills the viewport: .wrap's top padding above, its bottom padding cancelled by the negative margin */
.chat { display: grid; grid-template-columns: 240px minmax(0, 1fr); gap: 14px; height: calc(100dvh - 48px); min-height: 420px; margin-bottom: -36px; }
aside { display: flex; flex-direction: column; gap: 10px; background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); padding: 12px; min-height: 0; }
.new { justify-content: center; }
.list { display: flex; flex-direction: column; gap: 2px; overflow-y: auto; flex: 1; min-height: 0; }
.conv { position: relative; display: flex; flex-direction: column; gap: 1px; text-align: left; background: transparent; border: 0; border-radius: var(--radius-sm); padding: 7px 26px 7px 10px; color: var(--muted); font: inherit; cursor: pointer; }
.conv:hover { background: var(--panel-2); color: var(--text); }
.conv.on { background: var(--panel-2); color: var(--text); }
.conv .t { font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
@media (pointer: coarse) {
  .conv.on { padding-right: 112px; }
  .ca { min-width: 34px; height: 34px; font-size: 13px; }
}
.find { display: flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 0 8px; color: var(--faint); }
.find:focus-within { border-color: var(--accent); }
.find input { flex: 1; min-width: 0; border: 0; background: transparent; padding: 6px 0; font: inherit; font-size: 13px; color: var(--text); border-radius: 0; box-shadow: none; outline: none; -webkit-appearance: none; appearance: none; }
.glab { padding: 8px 10px 2px; text-transform: uppercase; letter-spacing: .04em; font-size: 10.5px; }
.conv .cacts { position: absolute; right: 4px; top: 50%; transform: translateY(-50%); display: none; gap: 1px; background: var(--panel-2); border-radius: 6px; }
.conv:hover .cacts, .conv.on .cacts { display: flex; }
.ca { display: grid; place-items: center; min-width: 22px; height: 22px; border: 0; background: none; border-radius: 5px; color: var(--muted); cursor: pointer; font-size: 11px; }
.ca:hover { color: var(--text); background: var(--line); }
.ca.lit { color: var(--accent); }
.ca.x:hover { color: var(--bad); }
.glab.fold { cursor: pointer; }
.mover { display: flex; flex-direction: column; gap: 2px; margin: 0 6px 6px; padding: 4px; background: var(--panel-2); border: 1px solid var(--line-2); border-radius: var(--radius-sm); }
.mover button { text-align: left; background: none; border: 0; color: var(--text); font: inherit; padding: 8px 8px; border-radius: 6px; cursor: pointer; }
.mover button.on { color: var(--accent); }
.mover button:hover { background: var(--accent-soft); }
.nf { display: flex; gap: 4px; }
.nf input { flex: 1; min-width: 0; font: inherit; font-size: 13px; padding: 6px 8px; }
.sortall { align-self: flex-start; padding: 0 10px; }
.arch { align-self: flex-start; margin: 8px 10px 0; }
.ctxw { position: relative; flex-shrink: 0; }
.ring { display: inline-flex; align-items: center; gap: 4px; padding: 4px 7px; }
.ring svg { transform: rotate(-90deg); }
.ring .rt { fill: none; stroke: var(--line-2); stroke-width: 3; }
.ring .rv { fill: none; stroke: var(--accent); stroke-width: 3; stroke-linecap: round; }
.ring.warn .rv { stroke: var(--warn); }
.ring.bad .rv { stroke: var(--bad); }
.ctxpop { position: absolute; right: 0; top: calc(100% + 6px); z-index: 30; width: 230px; display: flex; flex-direction: column; gap: 8px; padding: 12px; background: var(--panel-2); border: 1px solid var(--line-2); border-radius: var(--radius-sm); box-shadow: 0 8px 28px rgba(0, 0, 0, .45); }
.ctxpop .btn { align-self: flex-start; }
.cbar { height: 6px; border-radius: 3px; background: var(--track); overflow: hidden; }
.cbar span { display: block; height: 100%; background: var(--accent); }
.menuw { position: relative; flex-shrink: 0; }
.mbtn { font-size: 16px; padding: 2px 10px; }
.mbtn.on { color: var(--accent); background: var(--accent-soft); }
.menu { position: absolute; right: 0; top: calc(100% + 6px); z-index: 30; min-width: 220px; display: flex; flex-direction: column; padding: 4px; background: var(--panel-2); border: 1px solid var(--line-2); border-radius: var(--radius-sm); box-shadow: 0 8px 28px rgba(0, 0, 0, .45); }
.menu button { display: flex; align-items: center; justify-content: flex-start; gap: 8px; text-align: left; background: none; border: 0; color: var(--text); font: inherit; padding: 9px 10px; border-radius: 6px; cursor: pointer; }
.menu button > span:last-child:not(:first-child) { margin-left: auto; }
.menu button:hover:not(:disabled) { background: var(--accent-soft); }
.menu button:disabled { opacity: .45; cursor: default; }
.tasks { flex-shrink: 0; max-height: 60dvh; overflow-y: auto; border-top: 1px solid var(--line); padding: 12px; }
.queued { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; padding: 4px 0 14px; }
.qq { display: flex; align-items: center; gap: 6px; max-width: 85%; opacity: .6; }
.qb { background: var(--panel-2); border: 1px dashed var(--line-2); padding: 6px 12px; border-radius: 12px 12px 4px 12px; white-space: pre-wrap; overflow-wrap: anywhere; }
.webui { border-top: 1px solid var(--line); padding: 10px 2px 0; }
.main { position: relative; display: flex; flex-direction: column; background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); min-height: 0; min-width: 0; }
.mhead { display: flex; align-items: center; gap: 8px; padding: 10px 16px; border-bottom: 1px solid var(--line); min-height: 48px; }
.mhead > *:not(.ttl) { flex-shrink: 0; }
.ttl { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 600; }
.bodywrap { position: relative; flex: 1; min-height: 0; display: flex; flex-direction: column; }
.body { flex: 1; overflow-y: auto; padding: 4px 16px; min-height: 0; }
.dock { flex-shrink: 0; max-height: 55dvh; overflow-y: auto; border-top: 1px solid var(--line); padding: 8px 12px 10px; display: flex; flex-direction: column; gap: 6px; }
.dock.min { padding-bottom: 6px; }
.dhead { display: flex; align-items: center; gap: 8px; }
.dmin { margin-left: auto; font-size: 12px; padding: 2px 8px; }
.flash { color: var(--accent); padding: 2px 0 6px 31px; }
.bar { border-top: 1px solid var(--line); padding: 6px 8px 6px 12px; }
.autobtn { font-size: 12px; padding: 4px 10px; flex-shrink: 0; }
.autobtn.armed { color: var(--warn); background: var(--warn-soft); border-color: transparent; }
.bar select { padding: 5px 8px; font-size: 12px; }
@media (max-width: 640px) { .bar select { flex: 1 1 40%; font-size: 16px; } }
.clearbtn { font-size: 14px; padding: 4px 9px; flex-shrink: 0; }
.bar.armed { box-shadow: inset 0 2px 0 var(--warn); }
.cl { color: var(--claude); margin-right: 5px; }
.empty { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; padding: 30px 10px; text-align: center; }
.hero { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.hero b { color: var(--text); font-size: 16px; }
.hero .logo { display: grid; place-items: center; width: 48px; height: 48px; border-radius: var(--radius); font-size: 24px; margin-bottom: 6px; background: var(--accent-soft); color: var(--accent); }
.hero.claude .logo { background: color-mix(in srgb, var(--claude) 16%, transparent); color: var(--claude); }
.st { display: inline-flex; align-items: center; gap: 5px; flex-shrink: 0; }
.st .sd { width: 7px; height: 7px; border-radius: 50%; }
.st.busy { color: var(--accent); }
.st.busy .sd { background: var(--accent); animation: sdpulse 1.4s ease-in-out infinite; }
.st.input { color: var(--warn); }
.st.input .sd { background: var(--warn); box-shadow: 0 0 0 3px var(--warn-soft); }
@keyframes sdpulse { 50% { opacity: .3; transform: scale(.7); } }
.jump { position: absolute; right: 18px; bottom: 12px; z-index: 5; width: 34px; height: 34px; border-radius: 50%; border: 1px solid var(--line-2); background: var(--panel-2); color: var(--text); font-size: 16px; cursor: pointer; box-shadow: 0 4px 14px rgba(0, 0, 0, .35); }
.jump:hover { border-color: var(--faint); }
.examples { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; max-width: 560px; }
.examples .pill { cursor: pointer; font: inherit; font-size: 12px; padding: 4px 11px; }
.examples .pill:hover { color: var(--text); border-color: var(--faint); }
.only-phone, .only-phone-i, .menu button.only-phone { display: none; }
.scrim { display: none; }
@media (max-width: 760px) {
  .chat { grid-template-columns: minmax(0, 1fr); }
  aside {
    display: none; position: fixed; z-index: 60; left: 0; top: 0; bottom: 0; width: min(300px, 84vw);
    border-radius: 0 var(--radius) var(--radius) 0; border-left: 0; padding: 16px 12px calc(16px + env(safe-area-inset-bottom));
    box-shadow: 0 0 40px rgba(0, 0, 0, .6);
  }
  aside.open { display: flex; }
  .scrim { display: block; position: fixed; inset: 0; z-index: 55; background: rgba(0, 0, 0, .5); }
  .only-phone { display: inline-flex; padding: 4px 10px; font-size: 16px; }
  .menu button.only-phone { display: flex; padding: 9px 10px; font-size: inherit; }
  .mhead { gap: 4px; }
  .hide-phone { display: none; }
  .only-phone-i { display: inline; }
  .seg > button { padding: 6px 12px; font-size: 14px; }
  .autobtn, .clearbtn { padding: 4px 10px; font-size: 14px; }
  .mhead { padding: 6px 6px; }
  .body { padding: 4px 12px; }
  .conv { padding: 10px 40px 10px 10px; }
  .conv .x { opacity: 1; }
}
@media (max-width: 640px) {
  /* .wrap: 12px on top, 28px + tab bar below */
  .chat { height: calc(100dvh - 24px - var(--tabbar, 0px)); margin-bottom: -16px; min-height: 0; }
}
</style>

<style>
/* keyboard up on the chat page: the tab bar would only eat the space above it */
@media (max-width: 640px) { html.kb .tabs { display: none !important; } html.kb .wrap { padding-top: 6px; padding-bottom: 6px; } html.kb .chat { height: calc(var(--vvh, 100dvh) - 12px); margin-bottom: 0; } }
</style>
