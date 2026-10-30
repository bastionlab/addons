<script setup lang="ts">
/**
 * Hacker Terminal navigation: a shell prompt docked at the bottom. Type to filter pages (autocomplete above the
 * prompt, ↑/↓ + Enter, Tab completes, Esc closes), or use the little shell: cd, ls, help, pwd, whoami, find, clear,
 * exit, sudo (no), pin/unpin DIR. Above the prompt an `ls` row of tappable directories, so a phone never has to type:
 * the pinned ones (the viewer's pick, shared with every look) first and marked `*`; the `pin` chip edits them.
 * Live state is a systemd-style [ OK ]/[WARN]/[FAIL] tag (tap it for `systemctl status`). Also renders the CRT
 * overlay (scanlines + vignette) and the once-per-session boot log, both pointer-events: none.
 */
const props = withDefaults(defineProps<{
  nav?: { to: string, icon: string, label: string }[], path?: string
  badge?: (to: string) => number, mark?: (to: string) => string
  state?: string, stateText?: string, up?: string, full?: boolean
}>(), { nav: () => [], path: '/', badge: () => 0, mark: () => '', state: 'ok', stateText: '', up: '', full: false })
const emit = defineEmits<{ search: [] }>()
const { t } = useI18n()

const nav = computed(() => props.nav ?? [])
const { isPinned, toggle, editing, full: pinsFull, max, keys } = useNavPins(() => nav.value)
// ls row: pinned directories first, then the rest in nav order
const lsRow = computed(() => [...nav.value.filter(n => isPinned(n.to)), ...nav.value.filter(n => !isPinned(n.to))])
const slug = (to: string) => (to === '/' ? '~' : to.replace(/^\/+/, '').replace(/\/+$/, ''))
const cwd = computed(() => (props.path === '/' ? '~' : `~/${slug(props.path)}`))
const user = useState('skin-term-user', () => 'user')
const tag = computed(() => (props.state === 'bad' ? 'FAIL' : props.state === 'warn' ? 'WARN' : ' OK '))

// ---------- the prompt ----------
const input = ref<HTMLInputElement | null>(null)
const ls = ref<HTMLElement | null>(null)
const q = ref('')
const focused = ref(false)
const sel = ref(0)
const open = ref(false) // desktop full-screen pages: prompt collapsed to a corner button until opened
type Line = { text: string, kind?: 'echo' | 'err' | 'ok' | 'dim', links?: { to: string, text: string }[] }
const out = ref<Line[]>([])
const COMMANDS = ['pin', 'unpin', 'cd', 'ls', 'dir', 'help', '?', 'clear', 'cls', 'sudo', 'su', 'exit', 'logout', 'quit', 'whoami', 'pwd', 'find', 'search', 'grep', 'rm', 'systemctl', 'status']

const words = computed(() => q.value.trim().split(/\s+/).filter(Boolean))
const isCd = computed(() => words.value[0]?.toLowerCase() === 'cd')
const arg = computed(() => {
  const w = words.value
  if (!w.length) return ''
  if (isCd.value) return w.slice(1).join(' ').replace(/^~\/?/, '').replace(/^\.\//, '')
  if (COMMANDS.includes(w[0]!.toLowerCase())) return null
  return w.join(' ').replace(/^~\/?/, '')
})
function score(n: { to: string, label: string }, a: string) {
  const s = slug(n.to).toLowerCase()
  const l = n.label.toLowerCase()
  if (s === a || l === a) return 0
  if (s.startsWith(a) || l.startsWith(a)) return 1
  if (s.includes(a) || l.includes(a)) return 2
  return 9
}
const matches = computed(() => {
  const a = arg.value
  if (a === null) return []
  const lo = a.toLowerCase()
  if (!lo) return focused.value && !out.value.length ? nav.value.slice() : []
  return nav.value.map(n => ({ n, s: score(n, lo) })).filter(x => x.s < 9).sort((x, y) => x.s - y.s).map(x => x.n)
})
watch(matches, () => (sel.value = 0))
const showList = computed(() => focused.value && matches.value.length > 0)

function resolve(a: string) {
  const lo = a.replace(/^~\/?/, '').replace(/\/+$/, '').toLowerCase()
  if (!lo || lo === '~' || lo === '/' || lo === '..') return '/'
  const hit = nav.value.map(n => ({ n, s: score(n, lo) })).filter(x => x.s < 2).sort((x, y) => x.s - y.s)[0]
  return hit?.n.to ?? null
}
function print(...lines: Line[]) { out.value = [...out.value, ...lines].slice(-14) }
function go(to: string) {
  q.value = ''
  out.value = []
  input.value?.blur()
  open.value = false
  if (to !== props.path) navigateTo(to)
}
const pageLinks = () => nav.value.map(n => ({ to: n.to, text: `${slug(n.to)}/` }))
function run(raw: string) {
  const s = raw.trim()
  q.value = ''
  if (!s) return
  print({ text: `${user.value}@bastion:${cwd.value}$ ${s}`, kind: 'echo' })
  const [c0, ...rest] = s.split(/\s+/)
  const cmd = c0!.toLowerCase()
  const a = rest.join(' ')
  switch (cmd) {
    case 'cd': {
      const to = resolve(a)
      if (to) return go(to)
      return print({ text: t('skinTerminal.noDir', { dir: a }), kind: 'err' })
    }
    case 'ls': case 'dir':
      return print({ text: '', links: pageLinks() })
    case 'help': case '?':
      return print({ text: t('skinTerminal.helpHead'), kind: 'dim' }, { text: '', links: pageLinks() }, { text: t('skinTerminal.helpCmds'), kind: 'dim' })
    case 'clear': case 'cls':
      out.value = []
      return
    case 'sudo': case 'su': {
      const k = 1 + Math.floor(Math.random() * 3)
      return print({ text: t(`skinTerminal.sudo${k}`, { user: user.value }), kind: 'err' })
    }
    case 'rm':
      return print({ text: t('skinTerminal.rm'), kind: 'err' })
    case 'exit': case 'logout': case 'quit':
      print({ text: t('skinTerminal.logout'), kind: 'dim' })
      setTimeout(() => go('/'), 450)
      return
    case 'whoami':
      return print({ text: user.value })
    case 'pwd':
      return print({ text: `/home/${user.value}${cwd.value.slice(1)}` })
    case 'find': case 'search': case 'grep':
      out.value = []
      input.value?.blur()
      emit('search')
      return
    case 'systemctl': case 'status':
      return status()
    case 'pin': case 'unpin': {
      if (!a) { editing.value = cmd === 'pin'; return print({ text: t('skinTerminal.pinned', { list: keys.value.map(slug).join(' ') || '–', n: keys.value.length, max }), kind: 'dim' }) }
      const to = resolve(a)
      if (!to) return print({ text: t('skinTerminal.noDir', { dir: a }), kind: 'err' })
      if (isPinned(to) === (cmd === 'pin')) return print({ text: t('skinTerminal.pinned', { list: keys.value.map(slug).join(' '), n: keys.value.length, max }), kind: 'dim' })
      if (cmd === 'pin' && pinsFull.value) return print({ text: t('skinTerminal.pinFull', { max }), kind: 'err' })
      toggle(to)
      return print({ text: t('skinTerminal.pinned', { list: keys.value.map(slug).join(' '), n: keys.value.length, max }), kind: 'ok' })
    }
    default: {
      const to = resolve(s)
      if (to) return go(to)
      return print({ text: t('skinTerminal.notFound', { cmd: c0 }), kind: 'err' })
    }
  }
}
function status() {
  const st = props.state === 'ok' ? t('skinTerminal.agentOk') : (props.stateText || tag.value)
  print({ text: t('skinTerminal.status', { state: st, up: props.up || '–' }), kind: props.state === 'ok' ? 'ok' : 'err' })
}
function onKey(e: KeyboardEvent) {
  const m = matches.value
  if (e.key === 'ArrowDown' && m.length) { e.preventDefault(); sel.value = (sel.value + 1) % m.length }
  else if (e.key === 'ArrowUp' && m.length) { e.preventDefault(); sel.value = (sel.value - 1 + m.length) % m.length }
  else if (e.key === 'Tab' && m.length) {
    e.preventDefault()
    q.value = `${isCd.value ? 'cd ' : ''}${slug(m[sel.value]!.to)}`
  }
  else if (e.key === 'Enter') {
    e.preventDefault()
    const w0 = words.value[0]?.toLowerCase() ?? ''
    if (m.length && q.value.trim() && (isCd.value || !COMMANDS.includes(w0))) go(m[sel.value]!.to)
    else run(q.value)
  }
  else if (e.key === 'Escape') {
    if (q.value || out.value.length) { q.value = ''; out.value = [] }
    else { input.value?.blur(); open.value = false }
  }
}
function onFocus() { focused.value = true; trackKb(true) }
function onBlur() {
  // let a tap on a suggestion land before the list goes away
  setTimeout(() => { focused.value = false; trackKb(false) }, 160)
}
function openPrompt() { open.value = true; nextTick(() => input.value?.focus()) }

// phone keyboard: Chrome only shrinks the visual viewport, so lift the bar above the keyboard ourselves
const kb = ref(0)
function onVv() {
  const vv = window.visualViewport
  kb.value = vv ? Math.max(0, Math.round(window.innerHeight - vv.height - vv.offsetTop)) : 0
}
function trackKb(on: boolean) {
  const vv = window.visualViewport
  if (!vv) return
  if (on) { vv.addEventListener('resize', onVv); vv.addEventListener('scroll', onVv); onVv() }
  else { vv.removeEventListener('resize', onVv); vv.removeEventListener('scroll', onVv); kb.value = 0 }
}

// "/" anywhere (not while typing somewhere) jumps to the prompt
function onGlobalKey(e: KeyboardEvent) {
  if (e.key !== '/' || e.metaKey || e.ctrlKey || e.altKey) return
  const el = e.target as HTMLElement | null
  if (el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName))) return
  e.preventDefault()
  openPrompt()
}

// keep the open directory in view in the ls row
function reveal(smooth = true) {
  const r = ls.value
  const b = r?.querySelector<HTMLElement>('.on')
  if (!r || !b) return
  r.scrollTo({ left: Math.max(0, b.offsetLeft - (r.clientWidth - b.offsetWidth) / 2), behavior: smooth ? 'smooth' : 'auto' })
}
watch(() => props.path, () => { out.value = []; q.value = ''; editing.value = false; nextTick(() => reveal()) })

// ---------- boot log, once per session ----------
const boot = ref(false)
const BOOT = ['boot1', 'boot2', 'boot3', 'boot4', 'boot5', 'boot6', 'boot7']
let bootT: ReturnType<typeof setTimeout> | undefined

onMounted(() => {
  window.addEventListener('keydown', onGlobalKey)
  nextTick(() => reveal(false))
  if (user.value === 'user') {
    $fetch<any>('/api/account').then((a) => {
      const n = String(a?.user?.name ?? '').toLowerCase().replace(/[^a-z0-9_-]+/g, '').slice(0, 14)
      if (n) user.value = n
    }).catch(() => {})
  }
  try {
    if (!sessionStorage.getItem('skin-term:boot')) {
      sessionStorage.setItem('skin-term:boot', '1')
      if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        boot.value = true
        bootT = setTimeout(() => (boot.value = false), 1400)
      }
    }
  } catch {}
})
onUnmounted(() => {
  window.removeEventListener('keydown', onGlobalKey)
  trackKb(false)
  if (bootT) clearTimeout(bootT)
})
</script>

<template>
  <div class="tm-nav" :class="{ full, open, focus: focused }">
    <!-- the CRT glass over everything: scanlines, vignette, curved edge shading -->
    <div class="crt" aria-hidden="true" />

    <Transition name="tboot">
      <div v-if="boot" class="boot" aria-hidden="true">
        <p v-for="(k, i) in BOOT" :key="k" :style="{ animationDelay: `${i * 120}ms` }">
          <span class="ok">{{ '[  OK  ]' }}</span> {{ $t(`skinTerminal.${k}`) }}
        </p>
      </div>
    </Transition>

    <button v-if="full" type="button" class="corner" :aria-label="$t('skinTerminal.openPrompt')" @click="openPrompt">{{ '>_' }}</button>

    <div class="dock" :style="kb ? { transform: `translateY(${-kb}px)` } : undefined">
      <!-- scrollback + autocomplete float above the prompt -->
      <div v-if="out.length || showList" class="pop">
        <div v-if="out.length" class="out">
          <p v-for="(l, i) in out" :key="i" :class="l.kind">
            <template v-if="l.links">
              <button v-for="lk in l.links" :key="lk.to" type="button" class="lk" @mousedown.prevent @click="go(lk.to)">{{ lk.text }}</button>
            </template>
            <template v-else>{{ l.text }}</template>
          </p>
        </div>
        <ul v-if="showList" class="ac" role="listbox">
          <li v-for="(m, i) in matches" :key="m.to" role="option" :aria-selected="i === sel">
            <button type="button" :class="{ sel: i === sel }" @mousedown.prevent @click="go(m.to)" @pointerenter="sel = i">
              <span class="ar">{{ i === sel ? '>' : ' ' }}</span>
              <Icon :name="m.icon" :size="14" />
              <span class="sl">{{ slug(m.to) }}/</span>
              <span class="lb">{{ m.label }}</span>
              <span v-if="badge(m.to)" class="bd">{{ `(${badge(m.to)})` }}</span>
            </button>
          </li>
          <li class="hint">{{ $t('skinTerminal.hint') }}</li>
        </ul>
      </div>

      <!-- ls: tappable directories -->
      <nav ref="ls" class="ls" :aria-label="$t('skinTerminal.pages')">
        <button type="button" class="pin" :class="{ on: editing }" :aria-pressed="editing" @click="editing = !editing">{{ editing ? `pin ${keys.length}/${max} ✓` : 'pin' }}</button>
        <NuxtLink v-for="n in lsRow" v-show="!editing" :key="n.to" :to="n.to" class="dir" :class="{ on: n.to === path, pinned: isPinned(n.to) }">
          <span class="dn">{{ slug(n.to) }}/</span><span v-if="isPinned(n.to)" class="st">{{ '*' }}</span>
          <span v-if="badge(n.to)" class="bd">{{ badge(n.to) }}</span>
          <span v-else-if="mark(n.to)" class="mk" :class="mark(n.to)" />
        </NuxtLink>
        <button v-for="n in lsRow" v-show="editing" :key="'e' + n.to" type="button" :aria-pressed="isPinned(n.to)" class="dir" :class="{ pinned: isPinned(n.to), dim: pinsFull && !isPinned(n.to) }" @click="toggle(n.to)">
          <span class="dn">{{ slug(n.to) }}/</span><span v-if="isPinned(n.to)" class="st">{{ '*' }}</span>
          <span v-if="badge(n.to)" class="bd">{{ badge(n.to) }}</span>
          <span v-else-if="mark(n.to)" class="mk" :class="mark(n.to)" />
        </button>
      </nav>

      <!-- the prompt -->
      <div class="prompt" @click.self="input?.focus()">
        <button type="button" class="tag" :class="state" :title="stateText" @click="status">{{ `[${tag}]` }}</button>
        <label class="ps" for="tm-prompt">
          <span class="uh">{{ `${user}@bastion` }}</span><span class="co">{{ ':' }}</span><span class="cw">{{ cwd }}</span><span class="dl">{{ '$' }}</span>
        </label>
        <input
          id="tm-prompt" ref="input" v-model="q" class="in" type="text" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false"
          enterkeyhint="go" :placeholder="$t('skinTerminal.placeholder')" @keydown="onKey" @focus="onFocus" @blur="onBlur"
        >
        <span class="up">{{ up }}</span>
        <span class="jobs"><JobsButton /></span>
        <button type="button" class="ib" :aria-label="$t('skinTerminal.search')" @click="emit('search')"><Icon name="search" :size="20" /></button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tm-nav { --row: 36px; --pr: 46px; font-family: var(--tm-mono); }
/* ---------- CRT overlay ---------- */
.crt {
  position: fixed; inset: 0; z-index: 90; pointer-events: none;
  background:
    repeating-linear-gradient(180deg, rgba(0, 0, 0, 0) 0 2px, rgba(0, 0, 0, .16) 2px 3px),
    radial-gradient(130% 120% at 50% 50%, transparent 62%, rgba(0, 0, 0, .38) 100%);
  box-shadow: inset 0 0 90px rgba(0, 0, 0, .45), inset 0 0 6px rgba(57, 255, 106, .08);
  border-radius: 14px / 18px;
}

/* ---------- boot log ---------- */
.boot {
  position: fixed; inset: 0; z-index: 95; pointer-events: none; padding: calc(env(safe-area-inset-top, 0px) + 18px) 18px;
  background: rgba(1, 4, 2, .88); font-size: 13px; line-height: 1.55; color: var(--muted);
}
.boot p { margin: 0; opacity: 0; animation: tline .01s linear forwards; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.boot .ok { color: var(--ok); }
@keyframes tline { to { opacity: 1; } }
.tboot-leave-active { transition: opacity .3s, transform .3s; }
.tboot-leave-to { opacity: 0; transform: scaleY(.02); }

/* ---------- the dock ---------- */
.dock {
  position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; padding-bottom: env(safe-area-inset-bottom);
  background: rgba(1, 6, 3, .94); border-top: 1px solid var(--line-2);
  box-shadow: 0 -10px 30px rgba(0, 0, 0, .55), 0 -1px 0 rgba(57, 255, 106, .12);
  transition: transform .12s;
}
.ls {
  display: flex; gap: 2px; height: var(--row); align-items: center; padding: 0 8px; overflow-x: auto; scrollbar-width: none;
  border-bottom: 1px dashed var(--line); overscroll-behavior-x: contain;
}
.ls::-webkit-scrollbar { display: none; }
.dir {
  position: relative; flex: none; display: inline-flex; align-items: center; gap: 4px; height: 30px; padding: 0 8px;
  color: var(--accent); font-size: 13.5px; font-weight: 600; text-decoration: none; -webkit-tap-highlight-color: transparent;
}
.dir:hover { text-decoration: none; background: color-mix(in srgb, var(--accent) 14%, transparent); }
button.dir { background: none; border: 0; font-family: inherit; cursor: pointer; }
.dir .dn { color: inherit; }
.dir .st { margin-left: -3px; color: var(--warn); }
.dir.dim { opacity: .4; }
.pin {
  flex: none; height: 30px; padding: 0 8px; margin-right: 4px; background: none; border: 1px dashed var(--line-2); color: var(--muted);
  font: inherit; font-size: 12.5px; cursor: pointer; white-space: pre; -webkit-tap-highlight-color: transparent;
}
.pin.on { border-style: solid; border-color: var(--accent); color: var(--accent); }
button.dir.pinned { outline: 1px solid var(--accent); outline-offset: -1px; }
.dir.on { background: var(--accent); color: var(--bg); text-shadow: none; }
.dir.on .bd { color: var(--bg); }
.bd { color: var(--warn); font-size: 12px; font-weight: 700; }
.mk { width: 7px; height: 7px; background: var(--accent); }
.dir.on .mk { background: var(--bg); }
.mk.busy { animation: tblink 1s steps(1) infinite; }
.mk.input { background: var(--warn); }
@keyframes tblink { 50% { opacity: 0; } }

.prompt { display: flex; align-items: center; gap: 8px; height: var(--pr); padding: 0 8px 0 10px; font-size: 14px; }
.tag {
  flex: none; padding: 0 2px; height: 32px; background: none; border: 0; cursor: pointer; font: inherit; font-weight: 700; white-space: pre;
  color: var(--ok); text-shadow: 0 0 6px color-mix(in srgb, var(--ok) 60%, transparent);
}
.tag.warn { color: var(--warn); text-shadow: 0 0 6px color-mix(in srgb, var(--warn) 60%, transparent); }
.tag.bad { color: var(--bad); text-shadow: 0 0 6px color-mix(in srgb, var(--bad) 60%, transparent); animation: tblink 1.2s steps(1) infinite; }
.ps { flex: none; display: flex; min-width: 0; max-width: 46%; white-space: nowrap; cursor: text; font-weight: 700; }
.uh { color: var(--ok); }
.co { color: var(--text); }
.cw { color: color-mix(in srgb, var(--accent) 55%, rgb(120, 180, 255)); overflow: hidden; text-overflow: ellipsis; }
.dl { color: var(--text); margin-left: 1px; }
.in {
  flex: 1; min-width: 40px; height: 34px; padding: 0 8px !important; background: transparent !important; border: 0 !important; box-shadow: none !important;
  color: var(--text); font: inherit; font-size: 15px; caret-color: var(--accent); outline: none;
}
.in::placeholder { color: var(--faint); opacity: .8; }
.up { flex: none; color: var(--faint); font-size: 12px; white-space: nowrap; }
.jobs:empty { display: none; }
.jobs { flex: none; }
.ib { flex: none; display: grid; place-items: center; width: 36px; height: 36px; padding: 0; background: none; border: 1px solid transparent; color: var(--muted); cursor: pointer; }
.ib:hover { border-color: var(--line-2); color: var(--accent); }
.tm-nav :deep(.jt) { border-radius: 0; background: transparent; border-color: var(--line-2); color: var(--accent); }

/* ---------- scrollback + autocomplete ---------- */
.pop {
  position: absolute; left: 8px; right: 8px; bottom: calc(100% + 6px); max-width: 720px; max-height: min(52vh, 420px); overflow-y: auto;
  background: rgba(1, 6, 3, .97); border: 1px solid var(--line-2); box-shadow: 0 12px 40px rgba(0, 0, 0, .7), 0 0 18px rgba(57, 255, 106, .08);
  font-size: 13.5px;
}
.out { padding: 8px 10px; border-bottom: 1px dashed var(--line); }
.out:last-child { border-bottom: 0; }
.out p { margin: 0; line-height: 1.55; color: var(--text); white-space: pre-wrap; word-break: break-word; display: flex; flex-wrap: wrap; column-gap: 4px; }
.out p.echo { color: var(--muted); }
.out p.err { color: var(--bad); }
.out p.ok { color: var(--ok); }
.out p.dim { color: var(--faint); }
.lk { min-height: 30px; padding: 0 6px; background: none; border: 0; color: var(--accent); font: inherit; font-weight: 700; cursor: pointer; }
.lk:hover { background: var(--accent); color: var(--bg); }
.ac { list-style: none; margin: 0; padding: 4px 0; }
.ac button {
  display: flex; align-items: center; gap: 8px; width: 100%; min-height: 34px; padding: 0 10px; background: none; border: 0; text-align: left;
  color: var(--muted); font: inherit; cursor: pointer;
}
.ac button.sel { background: var(--accent); color: var(--bg); text-shadow: none; }
.ac button.sel .bd { color: var(--bg); }
.ar { width: 1ch; font-weight: 700; }
.sl { font-weight: 700; }
.lb { opacity: .75; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ac .bd { margin-left: auto; }
.hint { padding: 6px 10px 4px; font-size: 11.5px; color: var(--faint); border-top: 1px dashed var(--line); }

/* ---------- desktop full pages (/chat): the prompt folds into a corner key ---------- */
.corner {
  display: none; position: fixed; z-index: 61; left: 12px; bottom: 12px; width: 44px; height: 36px; padding: 0;
  background: var(--bg); border: 1px solid var(--accent); color: var(--accent); font: inherit; font-weight: 700; cursor: pointer;
  box-shadow: 0 0 14px rgba(57, 255, 106, .25);
}
@media (min-width: 641px) {
  .full .corner { display: block; }
  .full .dock { transform: translateY(110%); }
  .full.open .dock, .full.focus .dock { transform: none; }
}

@media (max-width: 640px) {
  .uh, .co, .up { display: none; }
  .ps { max-width: 34%; }
  .prompt { gap: 4px; padding: 0 4px 0 6px; }
  .in { font-size: 16px; }
  .pop { left: 4px; right: 4px; }
  .crt { border-radius: 0; }
  html.kb .tm-nav:not(.focus) .dock { display: none; }
}
@media (pointer: coarse) { .dir, .pin { height: 32px; } }
@media (prefers-reduced-motion: reduce) {
  .dock { transition: none; }
  .tag.bad, .mk.busy { animation: none; }
}
</style>

<style>
/* only while this skin is on: font, room for the dock, sticky offset for the window title bar */
html.skin-terminal {
  --tm-mono: "JetBrains Mono", "Fira Code", "Cascadia Code", "Ubuntu Mono", "DejaVu Sans Mono", "Droid Sans Mono", Menlo, Consolas, "Bastion Emoji", monospace;
  --ptabs-top: calc(36px + env(safe-area-inset-top, 0px));
}
html.skin-terminal body { font-family: var(--tm-mono); }
/* thin phosphor line icons */
html.skin-terminal svg.icon { stroke-width: 1.4; stroke-linecap: square; stroke-linejoin: miter; }
html.skin-terminal .shell.skinned { --tabbar: calc(84px + env(safe-area-inset-bottom)); }
html.skin-terminal main.wrap { padding-bottom: calc(var(--tabbar) + 28px); }
</style>
