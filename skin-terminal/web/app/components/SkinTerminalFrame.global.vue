<script setup lang="ts">
/**
 * Each page is a terminal window: a sticky title bar with the three window dots and "user@bastion: ~/page",
 * then the shell types `cd ~/page` with a blinking block cursor and answers with an `ls -ld`-style line.
 * Full-screen pages (/chat) keep all their height: no chrome there.
 */
const props = withDefaults(defineProps<{ path?: string, title?: string, icon?: string }>(), { path: '/', title: '', icon: '' })
const FULL = ['/chat']
const isFull = computed(() => FULL.includes(props.path))
const user = useState('skin-term-user', () => 'user')
const seg = computed(() => props.path.replace(/^\/+/, '').split('/')[0] ?? '')
const cwd = computed(() => (seg.value ? `~/${seg.value}` : '~'))
const cmd = computed(() => `cd ${cwd.value}`)

const n = ref(0)
const typing = computed(() => n.value < cmd.value.length)
const typed = computed(() => cmd.value.slice(0, n.value))
let timer: ReturnType<typeof setTimeout> | undefined
let reduced = false
function type() {
  if (timer) clearTimeout(timer)
  if (reduced) { n.value = cmd.value.length; return }
  n.value = 0
  const step = () => {
    if (n.value >= cmd.value.length) return
    n.value++
    timer = setTimeout(step, 26 + Math.random() * 40)
  }
  timer = setTimeout(step, 140)
}

const now = ref(new Date())
const stamp = computed(() => fmtDate(now.value, { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' }))
const size = computed(() => (props.title.length * 97 + 1337) % 9000 + 1000)
const lsLine = computed(() => `drwxr-x--- 2 ${user.value} bastion ${size.value} ${stamp.value} ${seg.value || '.'}/`)
const cols = ref(80)
const rows = ref(24)
function measure() { cols.value = Math.floor(window.innerWidth / 8.4); rows.value = Math.floor(window.innerHeight / 18) }

watch(() => props.path, () => { now.value = new Date(); type() })
onMounted(() => {
  reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  measure()
  window.addEventListener('resize', measure, { passive: true })
  type()
})
onUnmounted(() => { if (timer) clearTimeout(timer); window.removeEventListener('resize', measure) })
</script>

<template>
  <div class="tframe" :class="{ bare: isFull }">
    <template v-if="!isFull">
      <header class="tb">
        <span class="dots" aria-hidden="true"><i /><i /><i /></span>
        <span class="tt">{{ `${user}@bastion: ${cwd}` }}</span>
        <span class="sz">{{ `${cols}×${rows}` }}</span>
      </header>
      <div class="sh">
        <p class="cmd"><span class="ps">{{ '$' }}</span> <span class="ty">{{ typed }}</span><i class="cur" :class="{ idle: !typing }" /></p>
        <p class="ls" :class="{ on: !typing }"><span>{{ lsLine }}</span><span v-if="title" class="cm">{{ `  # ${title}` }}</span></p>
      </div>
    </template>
    <div class="body"><slot /></div>
  </div>
</template>

<style scoped>
.tframe { min-width: 0; font-family: var(--tm-mono); }
.tb {
  position: sticky; top: 0; z-index: 30; display: flex; align-items: center; gap: 12px; height: 36px; padding: 0 12px;
  margin: 0 -1px; background: linear-gradient(180deg, rgba(14, 34, 20, .97), rgba(6, 18, 10, .97));
  border: 1px solid var(--line-2); border-bottom-color: var(--line); color: var(--muted); font-size: 13px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, .4);
}
.dots { display: flex; gap: 7px; flex: none; }
.dots i { width: 11px; height: 11px; border-radius: 50%; background: rgba(255, 92, 92, .85); box-shadow: inset 0 -1px 2px rgba(0, 0, 0, .4); }
.dots i:nth-child(2) { background: rgba(255, 204, 51, .85); }
.dots i:nth-child(3) { background: rgba(57, 255, 106, .85); }
.tt { flex: 1; min-width: 0; text-align: center; font-weight: 700; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sz { flex: none; color: var(--faint); font-size: 11.5px; }
.body { min-width: 0; }
.sh { padding: 12px 2px 4px; margin-bottom: 14px; font-size: 15px; line-height: 1.5; }
.sh p { margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cmd { color: var(--text); font-weight: 700; font-size: 20px; }
.ps { color: var(--accent); }
.cur { display: inline-block; width: .6em; height: 1.05em; margin-left: 2px; vertical-align: -3px; background: var(--accent); box-shadow: 0 0 8px var(--accent); }
.cur.idle { animation: tcur 1.05s steps(1) infinite; }
@keyframes tcur { 50% { opacity: 0; } }
.ls { color: var(--muted); font-size: 12.5px; opacity: 0; transform: translateY(-3px); transition: opacity .2s, transform .2s; }
.ls.on { opacity: 1; transform: none; }
.cm { color: var(--faint); }
@media (min-width: 641px) {
  .tframe:not(.bare) { border: 1px solid var(--line-2); background: rgba(2, 8, 4, .55); box-shadow: 0 0 0 1px rgba(0, 0, 0, .6), 0 20px 60px rgba(0, 0, 0, .5); }
  .tframe:not(.bare) .tb { margin: -1px -1px 0; }
  .tframe:not(.bare) .sh, .tframe:not(.bare) .body { padding-left: 18px; padding-right: 18px; }
  .tframe:not(.bare) .body { padding-bottom: 20px; }
}
@media (max-width: 640px) {
  .tb { margin: -12px -12px 0; padding: 0 10px; border-left: 0; border-right: 0; padding-top: env(safe-area-inset-top, 0px); height: calc(36px + env(safe-area-inset-top, 0px)); }
  .sz { display: none; }
  .tt { text-align: left; }
  .cmd { font-size: 18px; }
}
@media (prefers-reduced-motion: reduce) {
  .cur.idle { animation: none; }
  .ls { transition: none; }
}
</style>

<style>
/* page change: the old page collapses like a CRT switching off, the new one flickers on */
html.skin-terminal .skin-terminal-leave-active { animation: tm-off .16s ease-in forwards; transform-origin: 50% 30%; }
html.skin-terminal .skin-terminal-enter-active { animation: tm-on .3s linear; transform-origin: 50% 30%; }
@keyframes tm-off { to { opacity: 0; transform: scale(1.02, .006); } }
@keyframes tm-on {
  0% { opacity: 0; transform: scale(1, .02); }
  30% { opacity: .9; transform: scale(1, 1); }
  42% { opacity: .25; }
  56% { opacity: 1; }
  68% { opacity: .55; }
  100% { opacity: 1; }
}
@media (min-width: 641px) {
  html.skin-terminal[data-page="chat"] main.wrap { padding-bottom: 24px; }
}
@media (prefers-reduced-motion: reduce) {
  html.skin-terminal .skin-terminal-leave-active { animation: none; transition: opacity .1s; }
  html.skin-terminal .skin-terminal-enter-active { animation: none; transition: opacity .12s; }
  html.skin-terminal .skin-terminal-leave-to, html.skin-terminal .skin-terminal-enter-from { opacity: 0; }
}
</style>
