<script setup lang="ts">
/** Full-screen terminal: a real `tmux attach` held open by the agent, rendered with xterm.js.
 *  Keystrokes go straight to the pty; closing only detaches (the session keeps running). */
import '@xterm/xterm/css/xterm.css'

// target shell = a fresh login shell (ShellsPanel); `session` names it, there is no project path
const props = defineProps<{ vmid: number, path?: string, target: 'preview' | 'cc' | 'ship' | 'shell', session?: string, title: string }>()
const emit = defineEmits<{ close: [] }>()

const host = ref<HTMLElement>()
const status = ref('connecting…')
const height = ref('100dvh')

let term: any, fit: any, es: EventSource | undefined, ro: ResizeObserver | undefined
let id = ''
let pos = 0
let closed = false
let size = { cols: 0, rows: 0 }

const post = (action: string, body: any) => $fetch(`/api/term/${action}`, { method: 'POST', body })

// keystrokes are posted in order, batched while one request is in flight
let pending = ''
let sending = false
async function flush() {
  if (sending || !pending || !id) return
  sending = true
  const data = pending
  pending = ''
  try { await post('input', { id, data }) } catch (e: any) { status.value = e?.data?.statusMessage || 'input failed' }
  sending = false
  if (pending) flush()
}
function type(data: string) { pending += data; flush() }

function connect() {
  es = new EventSource(`/api/term/stream?id=${encodeURIComponent(id)}&from=${pos}`)
  es.onmessage = (e) => {
    pos = Number(e.lastEventId) || pos
    const bin = atob(e.data)
    const bytes = new Uint8Array(bin.length)
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
    term.write(bytes)
    status.value = ''
  }
  es.addEventListener('end', () => { status.value = 'session ended'; es?.close() })
  es.onerror = () => {
    es?.close()
    if (closed || status.value === 'session ended') return
    status.value = 'reconnecting…'
    setTimeout(() => !closed && connect(), 1000)
  }
}

let resizeTimer: any
function refit() {
  const vv = window.visualViewport
  if (vv) height.value = `${vv.height}px` // keep above the phone keyboard
  clearTimeout(resizeTimer)
  resizeTimer = setTimeout(() => {
    if (!fit) return
    fit.fit()
    if (id && (term.cols !== size.cols || term.rows !== size.rows)) {
      size = { cols: term.cols, rows: term.rows }
      post('resize', { id, ...size }).catch(() => {})
    }
  }, 120)
}

onMounted(async () => {
  const [{ Terminal }, { FitAddon }, { Unicode11Addon }] = await Promise.all([
    import('@xterm/xterm'), import('@xterm/addon-fit'), import('@xterm/addon-unicode11')])
  // closed while the imports / font / attach were still loading: every await below checks, or the stream,
  // the tmux attach and the listeners outlive the component
  if (closed) return
  const phone = window.innerWidth < 640
  term = new Terminal({
    cursorBlink: true, fontSize: phone ? 12 : 13, scrollback: 2000, allowProposedApi: true,
    fontFamily: await termFont(),
    theme: { background: '#0a0c0f', foreground: '#d5d9e0' },
  })
  // tmux counts emoji like Claude Code's 🟡 / 🟢 as two cells; xterm's default (Unicode 6) as one, which shifted the
  // rest of that line by a cell
  if (closed) return term.dispose()
  term.loadAddon(new Unicode11Addon())
  term.unicode.activeVersion = '11'
  fit = new FitAddon()
  term.loadAddon(fit)
  term.open(host.value!)
  // WebGL paints all backgrounds before the text, so a Nerd Font icon may spill into the next cell like in a
  // real terminal; the default DOM renderer lets the neighbour's background cut it in half
  try {
    const { WebglAddon } = await import('@xterm/addon-webgl')
    const gl = new WebglAddon()
    gl.onContextLoss(() => gl.dispose())
    term.loadAddon(gl)
  } catch {}
  if (closed) return // onBeforeUnmount already disposed term
  fit.fit()
  size = { cols: term.cols, rows: term.rows }
  term.onData(type)
  term.focus()
  touchScroll(host.value!)
  try {
    const r: any = await post('open', { vmid: props.vmid, path: props.path, target: props.target, session: props.session, ...size })
    if (closed) { post('close', { id: r.id }).catch(() => {}); return }
    id = r.id
    connect()
    term.focus()
  } catch (e: any) {
    status.value = e?.data?.statusMessage || e?.message || 'could not attach'
  }
  ro = new ResizeObserver(refit)
  ro.observe(host.value!)
  window.visualViewport?.addEventListener('resize', refit)
  refit()
})

// xterm has no touch scrolling of its own (the canvas sits on top of its scroll viewport): turn a vertical swipe
// into scrollLines, with a little momentum; a tap without movement still focuses the keyboard
// Claude Code and friends run on the alternate screen, which has no xterm scrollback: then the wheel goes to tmux
// (SGR mouse events, tmux mouse is on for the attached window) and tmux scrolls its own history in copy-mode
let touchAt = { x: 0, y: 0 }
// the wheel event carries the cell under the finger, so tmux scrolls that lane (not always the top-left one)
function cellAt() {
  const d = term?._core?._renderService?.dimensions?.css?.cell
  const r = host.value?.querySelector('.xterm-screen')?.getBoundingClientRect()
  if (!d || !r) return { c: 1, r: 1 }
  return {
    c: Math.min(term.cols, Math.max(1, Math.floor((touchAt.x - r.left) / d.width) + 1)),
    r: Math.min(term.rows, Math.max(1, Math.floor((touchAt.y - r.top) / d.height) + 1)),
  }
}
function scroll(n: number) {
  if (term.buffer.active.type !== 'alternate') return term.scrollLines(n)
  const p = cellAt()
  const seq = n > 0 ? `\x1b[<65;${p.c};${p.r}M` : `\x1b[<64;${p.c};${p.r}M`
  type(seq.repeat(Math.min(Math.abs(n), 5)))
}

// select mode (toggle in the key row): a drag selects text instead of scrolling; Copy takes the selection
const selecting = ref(false)
let anchor = -1
// linear buffer position (row * cols + col) of a touch point, rows counted from the top of the scrollback
function posAt(x: number, y: number) {
  const d = term?._core?._renderService?.dimensions?.css?.cell
  const r = host.value?.querySelector('.xterm-screen')?.getBoundingClientRect()
  if (!d || !r) return 0
  const col = Math.min(term.cols - 1, Math.max(0, Math.floor((x - r.left) / d.width)))
  const row = Math.min(term.rows - 1, Math.max(0, Math.floor((y - r.top) / d.height)))
  return (term.buffer.active.viewportY + row) * term.cols + col
}
let selFrom = 0, selTo = -1
function selectTo(cur: number) {
  const from = Math.min(anchor, cur), to = Math.max(anchor, cur)
  selFrom = from; selTo = to
  term.select(from % term.cols, Math.floor(from / term.cols), to - from + 1)
}
async function copySel() {
  const text = selectedText()
  if (!text) { status.value = 'nothing selected: select mode, then drag over the text'; return }
  try { await navigator.clipboard.writeText(text) } catch {
    const ta = document.createElement('textarea')
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0'
    document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove()
  }
  status.value = `copied ${text.length} chars`
  term?.clearSelection()
  selTo = -1
}
// tmux repaints a pane as hard rows, so xterm can't tell a wrapped line from a real one: rebuild it. A row that fills
// the whole width continues the word on the next row (joined as is); a shorter row ended at a word break (joined with
// a space); an empty row is a real break and stays one.
function selectedText() {
  if (selTo < selFrom || !term?.getSelection()) return ''
  const cols = term.cols, buf = term.buffer.active
  let out = '', carry: 'none' | 'word' | 'space' = 'none'
  for (let r = Math.floor(selFrom / cols); r <= Math.floor(selTo / cols); r++) {
    const line = buf.getLine(r)
    if (!line) continue
    const sc = r === Math.floor(selFrom / cols) ? selFrom % cols : 0
    const ec = r === Math.floor(selTo / cols) ? (selTo % cols) + 1 : cols
    let seg = line.translateToString(true, sc, ec)
    if (!seg.trim()) { out += '\n'; carry = 'none'; continue }
    if (carry !== 'none') seg = seg.replace(/^\s+/, '')
    out += (carry === 'space' ? ' ' : '') + seg
    carry = line.translateToString(true).length >= cols ? 'word' : 'space'
  }
  return out.replace(/\n{3,}/g, '\n\n').trim()
}
function toggleSelect() {
  selecting.value = !selecting.value
  if (!selecting.value) term?.clearSelection()
  status.value = selecting.value ? 'select mode: drag over text, then Copy' : ''
}

function touchScroll(el: HTMLElement) {
  let y = 0, acc = 0, moved = false, vel = 0, last = 0, raf = 0
  const line = () => (term?._core?._renderService?.dimensions?.css?.cell?.height as number) || 16
  el.addEventListener('touchstart', (e) => {
    cancelAnimationFrame(raf)
    touchAt = { x: e.touches[0].clientX, y: e.touches[0].clientY }
    y = e.touches[0].clientY; acc = 0; moved = false; vel = 0; last = e.timeStamp
    if (selecting.value) { anchor = posAt(touchAt.x, touchAt.y); selectTo(anchor) }
  }, { passive: true })
  el.addEventListener('touchmove', (e) => {
    if (selecting.value) {
      if (e.cancelable) e.preventDefault()
      if (anchor >= 0) selectTo(posAt(e.touches[0].clientX, e.touches[0].clientY))
      return
    }
    const ny = e.touches[0].clientY
    const dy = y - ny
    y = ny
    if (Math.abs(dy) > 0) moved = true
    acc += dy
    const n = Math.trunc(acc / line())
    if (n) { scroll(n); acc -= n * line() }
    const dt = Math.max(1, e.timeStamp - last); last = e.timeStamp
    vel = dy / dt
    if (e.cancelable) e.preventDefault()
  }, { passive: false })
  // select mode: swallow the tap that would follow, it would focus the terminal and pop the keyboard up
  el.addEventListener('touchend', (e) => { if (selecting.value && e.cancelable) e.preventDefault() }, { passive: false })
  el.addEventListener('touchend', () => {
    if (selecting.value) return
    let v = vel * 16 // px per frame
    const step = () => {
      if (Math.abs(v) < 0.5 || closed) return
      acc += v; v *= 0.94
      const n = Math.trunc(acc / line())
      if (n) { scroll(n); acc -= n * line() }
      raf = requestAnimationFrame(step)
    }
    if (moved) step()
  }, { passive: true })
}

function close() {
  if (closed) return
  closed = true
  es?.close()
  if (id) post('close', { id }).catch(() => {})
  emit('close')
}
onBeforeUnmount(() => {
  ro?.disconnect()
  window.visualViewport?.removeEventListener('resize', refit)
  clearTimeout(resizeTimer)
  close()
  term?.dispose()
  fit = undefined
})

// keys a phone keyboard does not have
const KEYS: [string, string][] = [
  ['Esc', '\x1b'], ['Tab', '\t'], ['⇧Tab', '\x1b[Z'], ['↑', '\x1b[A'], ['↓', '\x1b[B'], ['←', '\x1b[D'], ['→', '\x1b[C'], ['^C', '\x03'],
]
// the ship session has a conductor and a lanes window: tmux prefix + n / p switches, + z zooms a lane.
// The agent attaches through a grouped view session, so n / p only move this view; o / z act on the shared window.
const SHIP_KEYS: [string, string][] = [['win ›', '\x02n'], ['‹ win', '\x02p'], ['pane', '\x02o'], ['zoom', '\x02z']]
// phone: 4 lanes side by side are ~12 columns each, so zoom (one lane full screen) and pane (next lane) come first
const narrow = typeof window !== 'undefined' && window.innerWidth < 640
const keys = computed(() => (props.target !== 'ship' ? KEYS : narrow ? [SHIP_KEYS[3], ...SHIP_KEYS.slice(0, 2), ...KEYS] : [...KEYS, ...SHIP_KEYS]))
const press = (seq: string) => { type(seq); term?.focus() }
</script>

<template>
  <div class="full" :style="{ height }">
      <div class="bar">
        <b class="mono">{{ title }}</b>
        <span v-if="status" class="small muted">{{ status }}</span>
        <button class="btn sm closebtn" title="detach — the session keeps running" @click="close"><Icon name="x" :size="16"/> Close</button>
      </div>
      <div ref="host" class="xt" @click="!selecting && term?.focus()" />
      <div class="keys">
        <button v-for="[label, seq] in keys" :key="label" class="key mono" @mousedown.prevent @click="press(seq)">{{ label }}</button>
        <button class="key mono" :class="{ on: selecting }" @mousedown.prevent @click="toggleSelect">select</button>
        <button class="key mono" @mousedown.prevent @click="copySel">copy</button>
      </div>
  </div>
</template>

<style scoped>
.full { position: fixed; top: 0; left: 0; width: 100vw; z-index: 1000; background: var(--term-bg); display: flex; flex-direction: column; }
.tf-enter-active { transition: opacity var(--dur) var(--ease-out); }
.tf-leave-active { transition: opacity var(--dur-fast) var(--ease-in); }
.tf-enter-from, .tf-leave-to { opacity: 0; }
.bar { display: flex; align-items: center; gap: 10px; padding: 6px 10px; background: var(--panel); border-bottom: 1px solid var(--line); }
.bar b { font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.closebtn { margin-left: auto; }
.xt { flex: 1; min-height: 0; padding: 4px 6px; touch-action: none; overscroll-behavior: contain; }
.keys { display: flex; gap: 4px; padding: 5px 6px; border-top: 1px solid var(--line); background: var(--term-bg); overflow-x: auto; }
.key { flex: 1; background: var(--panel-2); color: var(--muted); border: 1px solid var(--line-2); border-radius: 6px; font-size: 12.5px; padding: 6px 0; min-width: 38px; cursor: pointer; }
@media (pointer: coarse) { .key { min-height: 36px; } }
.key.on { color: var(--text); border-color: var(--accent); background: var(--accent-soft, var(--panel-2)); }
.key:hover { color: var(--text); border-color: var(--accent); }
</style>
