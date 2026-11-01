<script setup lang="ts">
/**
 * Navigation as a centred taskbar (phone and desktop): start button + every page as an icon in the middle with a
 * pill under the open one (phone: only the viewer's pinned pages + the open one; "Edit taskbar" in Start picks them), the tray on the right (jobs, live dot, clock). Start opens a flyout with a page filter,
 * the pinned grid of all pages and a footer. Props are the layout's own (layouts/default.vue → useSkinned('Nav')).
 */
const props = withDefaults(defineProps<{
  nav?: { to: string, icon: string, label: string }[], path?: string
  badge?: (to: string) => number, mark?: (to: string) => string
  state?: string, stateText?: string, up?: string, full?: boolean
}>(), { nav: () => [], path: '/', badge: () => 0, mark: () => '', state: 'ok', stateText: '', up: '', full: false })
const emit = defineEmits<{ search: [] }>()

const open = ref(false)
const q = ref('')
const field = ref<HTMLInputElement | null>(null)
const strip = ref<HTMLElement | null>(null)
const hits = computed(() => {
  const s = q.value.trim().toLowerCase()
  return s ? props.nav.filter(n => n.label.toLowerCase().includes(s)) : props.nav
})
const { isPinned, toggle: togglePin, editing, full: pinsFull, max, keys } = useNavPins(() => props.nav)
const totalBadge = computed(() => props.nav.reduce((s, n) => s + (props.badge(n.to) || 0), 0))

function toggle() {
  open.value = !open.value
  if (open.value) {
    q.value = ''
    // a phone keyboard popping up over the menu is worse than one more tap
    if (window.matchMedia('(pointer: fine)').matches) nextTick(() => field.value?.focus())
  }
}
function go(to: string) { if (editing.value) return togglePin(to); open.value = false; navigateTo(to) }
watch(open, v => { if (!v) editing.value = false })
function enter() { const first = hits.value[0]; if (first) go(first.to) }
function searchAll() { open.value = false; emit('search') }

// keep the open page's icon in view when the strip scrolls (phone with many pages)
function reveal() {
  nextTick(() => {
    const el = strip.value?.querySelector('.app.on') as HTMLElement | null
    el?.scrollIntoView({ block: 'nearest', inline: 'center' })
  })
}
watch(() => props.path, () => { open.value = false; reveal() })

const now = ref(new Date())
let t: ReturnType<typeof setInterval> | undefined
const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') open.value = false }
onMounted(() => {
  t = setInterval(() => (now.value = new Date()), 15_000)
  window.addEventListener('keydown', onKey)
  reveal()
})
onUnmounted(() => { clearInterval(t); window.removeEventListener('keydown', onKey) })
const clock = computed(() => now.value.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }))
const date = computed(() => now.value.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' }))
</script>

<template>
  <div class="w11-nav">
    <Transition name="w11-scrim"><div v-if="open" class="scrim" @click="open = false" /></Transition>
    <Transition name="w11-start">
      <div v-if="open" class="startmenu" role="dialog" :aria-label="$t('skinWin11.start')">
        <div class="find">
          <Icon name="search" :size="16" class="fi" />
          <input ref="field" v-model="q" type="search" :placeholder="$t('skinWin11.searchPages')" :aria-label="$t('skinWin11.searchPages')" @keydown.enter.prevent="enter">
          <button type="button" class="all" :aria-label="$t('skinWin11.searchAll')" @click="searchAll"><Icon name="spark" :size="15" /><span class="al">{{ $t('skinWin11.searchAll') }}</span></button>
        </div>
        <div class="head">
          <b>{{ editing ? $t('skinWin11.pinHint', { n: keys.length, max }) : $t('skinWin11.pinned') }}</b>
          <button type="button" class="edit" :class="{ on: editing }" :aria-pressed="editing" @click="editing = !editing">{{ editing ? $t('skinWin11.done') : $t('skinWin11.editTabs') }}<Icon v-if="!editing" name="pin" :size="13" /></button>
        </div>
        <div class="pins">
          <button v-for="n in hits" :key="n.to" type="button" class="pin" :class="{ on: n.to === path && !editing, tb: editing && isPinned(n.to), dim: editing && pinsFull && !isPinned(n.to) }" @click="go(n.to)">
            <span class="pi"><Icon :name="n.icon" :size="22" /></span>
            <span class="pl">{{ n.label }}</span>
            <span v-if="editing && isPinned(n.to)" class="pmark"><Icon name="pin" :size="11" /></span>
            <span v-else-if="badge(n.to)" class="badge">{{ badge(n.to) }}</span>
            <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
          </button>
          <p v-if="!hits.length" class="none">{{ $t('skinWin11.noMatch') }}</p>
        </div>
        <div class="foot">
          <span class="me"><span class="av">{{ 'b' }}</span><b>{{ 'bastion' }}</b></span>
          <span class="upt"><span class="dot" :class="state" />{{ up }}</span>
        </div>
      </div>
    </Transition>

    <nav class="taskbar">
      <div ref="strip" class="mid">
        <div class="apps">
          <button type="button" class="app start" :class="{ down: open }" :aria-expanded="open" :aria-label="$t('skinWin11.start')" @click="toggle">
            <svg class="quad" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
              <defs>
                <linearGradient id="w11-quad-a" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8fdcff" /><stop offset="1" stop-color="#2a8fe0" /></linearGradient>
                <linearGradient id="w11-quad-b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6cc8ff" /><stop offset="1" stop-color="#1c6fd0" /></linearGradient>
              </defs>
              <rect x="2.5" y="2.5" width="8.8" height="8.8" rx="1.6" fill="url(#w11-quad-a)" />
              <rect x="12.7" y="2.5" width="8.8" height="8.8" rx="1.6" fill="url(#w11-quad-b)" />
              <rect x="2.5" y="12.7" width="8.8" height="8.8" rx="1.6" fill="url(#w11-quad-b)" />
              <rect x="12.7" y="12.7" width="8.8" height="8.8" rx="1.6" fill="url(#w11-quad-a)" />
            </svg>
            <span v-if="totalBadge && !open" class="badge">{{ totalBadge }}</span>
          </button>
          <button type="button" class="app srch" :aria-label="$t('skinWin11.search')" @click="emit('search')"><Icon name="search" :size="19" /></button>
          <NuxtLink v-for="n in nav" :key="n.to" :to="n.to" class="app" :class="{ on: n.to === path, unpinned: !isPinned(n.to) && n.to !== path }" :aria-label="n.label" :title="n.label">
            <Icon :name="n.icon" :size="20" />
            <span v-if="badge(n.to)" class="badge">{{ badge(n.to) }}</span>
            <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
            <span class="ind" />
          </NuxtLink>
        </div>
      </div>
      <div class="tray">
        <JobsButton />
        <span class="dot" :class="state" :title="stateText" />
        <span class="clock"><span>{{ clock }}</span><span class="date">{{ date }}</span></span>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.taskbar {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 60; display: flex; align-items: center; gap: 6px;
  height: calc(52px + env(safe-area-inset-bottom)); padding: 0 8px env(safe-area-inset-bottom);
  background: color-mix(in srgb, var(--bg) 72%, transparent); backdrop-filter: blur(28px) saturate(1.5); -webkit-backdrop-filter: blur(28px) saturate(1.5);
  border-top: 1px solid rgba(255, 255, 255, .08);
}
/* the icon strip: centred while it fits, scrolls from the left once it doesn't */
.mid { flex: 1; min-width: 0; display: flex; overflow-x: auto; scrollbar-width: none; }
.mid::-webkit-scrollbar { display: none; }
.apps { display: flex; align-items: center; gap: 3px; margin: 0 auto; padding: 0 4px; }
.app {
  position: relative; flex: none; display: grid; place-items: center; width: 42px; height: 42px; border-radius: 6px;
  color: var(--text); background: transparent; border: 0; cursor: pointer; transition: background .15s, transform .1s;
  -webkit-tap-highlight-color: transparent;
}
.app:hover { background: rgba(255, 255, 255, .08); text-decoration: none; }
.app:active { transform: scale(.92); }
.app.on, .app.down { background: rgba(255, 255, 255, .1); }
.app.on :deep(svg) { color: var(--accent); }
.quad { transition: transform .2s cubic-bezier(.1, .9, .2, 1); }
.start:active .quad { transform: scale(.85); }
.ind { position: absolute; bottom: 2px; left: 50%; width: 6px; height: 3px; border-radius: 3px; background: var(--faint); opacity: 0; transform: translateX(-50%); transition: width .25s cubic-bezier(.1, .9, .2, 1), opacity .2s, background .2s; }
.app.on .ind { opacity: 1; width: 16px; background: var(--accent); }
.badge { position: absolute; top: 2px; right: 1px; min-width: 16px; padding: 0 4px; border-radius: 8px; font-size: 10px; font-weight: 600; line-height: 16px; text-align: center; color: var(--bg); background: var(--bad); }
.cm { position: absolute; top: 6px; right: 6px; width: 8px; height: 8px; border-radius: 50%; background: var(--accent); }
.cm.busy { animation: w11pulse 1.4s ease-in-out infinite; }
.cm.input { background: var(--warn); }
@keyframes w11pulse { 50% { opacity: .35; transform: scale(.7); } }
.tray { flex: none; display: flex; align-items: center; gap: 10px; padding-left: 4px; font-size: 12px; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ok); flex: none; }
.dot.warn { background: var(--warn); } .dot.bad { background: var(--bad); }
.clock { display: flex; flex-direction: column; align-items: flex-end; line-height: 1.3; padding: 4px 6px; border-radius: 6px; }
.clock:hover { background: rgba(255, 255, 255, .06); }

.scrim { position: fixed; inset: 0; z-index: 61; background: rgba(0, 0, 0, .18); }
.startmenu {
  position: fixed; z-index: 62; left: 50%; bottom: calc(60px + env(safe-area-inset-bottom)); transform: translateX(-50%);
  width: min(600px, calc(100vw - 16px)); max-height: calc(100dvh - 90px - env(safe-area-inset-bottom)); display: flex; flex-direction: column;
  border-radius: 10px; border: 1px solid rgba(255, 255, 255, .1); overflow: hidden;
  background: color-mix(in srgb, var(--panel) 82%, transparent); backdrop-filter: blur(40px) saturate(1.6); -webkit-backdrop-filter: blur(40px) saturate(1.6);
  box-shadow: 0 24px 64px rgba(0, 0, 0, .5), 0 2px 8px rgba(0, 0, 0, .3);
}
.find { position: relative; display: flex; gap: 8px; margin: 20px 22px 6px; }
.find .fi { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--faint); pointer-events: none; }
.find input {
  flex: 1; min-width: 0; height: 38px; padding: 0 12px 0 36px; font: inherit; color: var(--text); border-radius: 19px;
  background: color-mix(in srgb, var(--bg) 70%, transparent); border: 1px solid rgba(255, 255, 255, .08); border-bottom: 2px solid var(--accent); outline: none;
}
.all { flex: none; display: inline-flex; align-items: center; gap: 6px; height: 38px; padding: 0 12px; border-radius: 19px; font: inherit; font-size: 13px; color: var(--text); background: rgba(255, 255, 255, .06); border: 1px solid rgba(255, 255, 255, .08); cursor: pointer; }
.all:hover { background: rgba(255, 255, 255, .12); }
.head { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 12px 34px 6px; font-size: 13.5px; }
.edit { display: inline-flex; align-items: center; gap: 6px; min-height: 30px; padding: 0 10px; border-radius: 4px; border: 1px solid rgba(255, 255, 255, .08); background: rgba(255, 255, 255, .06); color: var(--text); font: inherit; font-size: 12px; cursor: pointer; }
.edit:hover { background: rgba(255, 255, 255, .1); }
.edit.on { background: var(--accent); border-color: var(--accent); color: var(--bg); }
.pin.tb { background: color-mix(in srgb, var(--accent) 16%, transparent); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--accent) 55%, transparent); }
.pin.dim { opacity: .4; }
.pmark { position: absolute; top: 6px; right: calc(50% - 30px); display: grid; place-items: center; width: 18px; height: 18px; border-radius: 50%; background: var(--accent); color: var(--bg); }
.pins { flex: 1; min-height: 0; overflow-y: auto; display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 4px; padding: 4px 22px 18px; align-content: start; }
.pin {
  position: relative; display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 12px 2px 10px; border-radius: 6px;
  font: inherit; font-size: 12px; color: var(--text); background: none; border: 0; cursor: pointer;
}
.pin:hover, .pin:focus-visible { background: rgba(255, 255, 255, .07); outline: none; }
.pin.on { background: rgba(255, 255, 255, .1); }
.pi { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 8px; color: var(--accent); background: linear-gradient(160deg, color-mix(in srgb, var(--accent) 22%, transparent), color-mix(in srgb, var(--accent) 6%, transparent)); }
.pl { max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pin .badge { top: 6px; right: calc(50% - 30px); }
.pin .cm { top: 8px; right: calc(50% - 26px); }
.none { grid-column: 1 / -1; margin: 10px 12px; color: var(--faint); }
.foot { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 12px 34px; background: rgba(0, 0, 0, .18); border-top: 1px solid rgba(255, 255, 255, .06); font-size: 13px; }
.me { display: flex; align-items: center; gap: 10px; }
.av { display: grid; place-items: center; width: 30px; height: 30px; border-radius: 50%; background: linear-gradient(135deg, var(--accent), color-mix(in srgb, var(--accent) 40%, var(--bg))); color: var(--bg); font-weight: 700; }
.upt { display: flex; align-items: center; gap: 8px; color: var(--muted); }

.w11-start-enter-active { transition: transform .28s cubic-bezier(.1, .9, .2, 1), opacity .2s; }
.w11-start-leave-active { transition: transform .15s ease-in, opacity .15s; }
.w11-start-enter-from, .w11-start-leave-to { opacity: 0; transform: translate(-50%, 40px); }
.w11-scrim-enter-active, .w11-scrim-leave-active { transition: opacity .2s; }
.w11-scrim-enter-from, .w11-scrim-leave-to { opacity: 0; }

@media (max-width: 640px) {
  .taskbar { padding: 0 4px env(safe-area-inset-bottom); gap: 2px; }
  .srch, .date { display: none; }
  .app { width: 40px; height: 44px; }
  .tray { gap: 6px; }
  .pins { grid-template-columns: repeat(4, minmax(0, 1fr)); padding: 4px 10px 14px; }
  .find { margin: 14px 12px 4px; }
  .all .al { display: none; }
  .all { width: 38px; padding: 0; justify-content: center; }
  .head { padding: 10px 22px 4px; }
  .foot { padding: 10px 18px; }
}
@media (prefers-reduced-motion: reduce) {
  .w11-start-enter-active, .w11-start-leave-active, .ind, .cm.busy { transition: none; animation: none; }
}
</style>

<style>
/* the page makes room for the taskbar; only while this skin is on */
html.skin-win11 .shell.skinned { --tabbar: calc(52px + env(safe-area-inset-bottom)); }
html.skin-win11 main.wrap { padding-bottom: calc(76px + env(safe-area-inset-bottom)); }
html.skin-win11 body { font-family: "Segoe UI Variable", "Segoe UI", system-ui, -apple-system, Roboto, sans-serif; background: transparent; }
@media (max-width: 640px) {
  html.skin-win11.kb .w11-nav .taskbar { display: none; }
  html.skin-win11 .w11-nav .app.unpinned { display: none; }
}
/* Fluent-style line icons: thin, rounded */
html.skin-win11 svg.icon { stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; }
</style>
