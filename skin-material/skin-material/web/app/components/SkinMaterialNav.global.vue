<script setup lang="ts">
/**
 * Material 3 navigation. Phone: a top app bar (menu → modal navigation drawer, the page title once the large
 * headline has scrolled away, search) and a bottom navigation bar with the viewer's pinned pages ("Edit bottom bar"
 * in the drawer). Desktop: a navigation
 * rail with a search FAB on top and jobs + live state at the bottom.
 * While the skin is on, .btn / .chip / nav items / panel headers get an M3 ripple (one pointerdown listener).
 */
const props = withDefaults(defineProps<{
  nav?: { to: string, icon: string, label: string }[], path?: string
  badge?: (to: string) => number, mark?: (to: string) => string
  state?: string, stateText?: string, up?: string, full?: boolean
}>(), { nav: () => [], path: '/', badge: () => 0, mark: () => '', state: 'ok', stateText: '', up: '', full: false })
const emit = defineEmits<{ search: [] }>()

const drawer = ref(false)
const here = computed(() => props.nav.find(n => n.to === props.path))
const { pinned: bottom, isPinned, toggle, editing, full: pinsFull, max, keys } = useNavPins(() => props.nav)
watch(drawer, v => { if (!v) editing.value = false })
const scrolled = ref(false)
const top = ref(true) // at the very top the bar is see-through, so it doesn't cut the backdrop shapes
let raf = 0
function onScroll() {
  if (raf) return
  raf = requestAnimationFrame(() => { raf = 0; scrolled.value = window.scrollY > 56; top.value = window.scrollY < 2 })
}
watch(() => props.path, () => { drawer.value = false; nextTick(onScroll) })
function search() { drawer.value = false; emit('search') }
const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') drawer.value = false }

// M3 ripple: a circle grows from the touch point inside the touched control, then fades. It lives in a fixed,
// clipped box over the control, so the control's own styles are never touched.
const RIPPLE = '.btn, .chip, .seg > button, .m3-item, .m3-panel > header, .m3-rip'
function ripple(e: PointerEvent) {
  if (e.pointerType === 'mouse' && e.button !== 0) return
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  const el = (e.target as Element | null)?.closest?.(RIPPLE) as HTMLElement | null
  if (!el || (el as HTMLButtonElement).disabled) return
  const r = el.getBoundingClientRect()
  if (!r.width || !r.height) return
  const cs = getComputedStyle(el)
  const size = 2 * Math.hypot(Math.max(e.clientX - r.left, r.right - e.clientX), Math.max(e.clientY - r.top, r.bottom - e.clientY))
  const box = document.createElement('span')
  box.className = 'm3-ripple-box'
  Object.assign(box.style, { left: `${r.left}px`, top: `${r.top}px`, width: `${r.width}px`, height: `${r.height}px`, borderRadius: cs.borderRadius })
  const dot = document.createElement('span')
  dot.className = 'm3-ripple-dot'
  Object.assign(dot.style, { width: `${size}px`, height: `${size}px`, left: `${e.clientX - r.left - size / 2}px`, top: `${e.clientY - r.top - size / 2}px`, background: cs.color })
  box.appendChild(dot)
  document.body.appendChild(box)
  setTimeout(() => box.remove(), 700)
}

onMounted(() => {
  window.addEventListener('keydown', onKey)
  window.addEventListener('scroll', onScroll, { passive: true })
  document.addEventListener('pointerdown', ripple, { passive: true })
  onScroll()
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  window.removeEventListener('scroll', onScroll)
  document.removeEventListener('pointerdown', ripple)
  if (raf) cancelAnimationFrame(raf)
  document.querySelectorAll('.m3-ripple-box').forEach(b => b.remove())
})
</script>

<template>
  <div class="m3-nav" :class="{ full }">
    <!-- phone: top app bar -->
    <header v-if="!full" class="m3-top" :class="{ scrolled, top }">
      <span class="m3-title" :class="{ show: scrolled || !here }">{{ here?.label ?? 'bastion' }}</span>
      <JobsButton />
      <button type="button" class="m3-icon m3-rip" :aria-label="$t('skinMaterial.search')" @click="search"><Icon name="search" :size="22" /></button>
    </header>

    <!-- phone: bottom navigation bar -->
    <nav class="m3-bar">
      <NuxtLink v-for="n in bottom" :key="n.to" :to="n.to" class="m3-item m3-dest" :class="{ on: n.to === path }">
        <span class="ind">
          <span class="pill" />
          <Icon :name="n.icon" :size="24" class="ic" />
          <span v-if="badge(n.to)" class="bdg">{{ badge(n.to) }}</span>
          <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
        </span>
        <span class="lbl">{{ n.label }}</span>
      </NuxtLink>
      <button type="button" class="m3-item m3-dest" :aria-label="$t('skinMaterial.menu')" :aria-expanded="drawer" @click="drawer = true">
        <span class="ind"><span class="pill" /><Icon name="grid" :size="24" class="ic" /></span>
        <span class="lbl">{{ $t('skinMaterial.pages') }}</span>
      </button>
    </nav>

    <!-- desktop: navigation rail -->
    <aside class="m3-rail">
      <button type="button" class="m3-fab m3-rip" :aria-label="$t('skinMaterial.search')" @click="search"><Icon name="search" :size="24" /></button>
      <nav class="rail-list">
        <NuxtLink v-for="n in nav" :key="n.to" :to="n.to" class="m3-item m3-dest" :class="{ on: n.to === path }">
          <span class="ind">
            <span class="pill" />
            <Icon :name="n.icon" :size="22" class="ic" />
            <span v-if="badge(n.to)" class="bdg">{{ badge(n.to) }}</span>
            <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
          </span>
          <span class="lbl">{{ n.label }}</span>
        </NuxtLink>
      </nav>
      <div class="rail-foot">
        <JobsButton />
        <span class="st" :title="stateText"><span class="dot" :class="state" />{{ up }}</span>
      </div>
    </aside>

    <!-- modal navigation drawer -->
    <Transition name="m3d">
      <div v-if="drawer" class="m3-scrim" @click.self="drawer = false">
        <aside class="m3-drawer" role="dialog" aria-modal="true" :aria-label="$t('skinMaterial.pages')">
          <div class="dh">
            <span class="brand">{{ 'bastion' }}</span>
            <button type="button" class="m3-icon m3-rip" :aria-label="$t('skinMaterial.close')" @click="drawer = false">
              <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none" /></svg>
            </button>
          </div>
          <div class="dstate"><span class="dot" :class="state" />{{ up }} · {{ stateText }}</div>
          <button type="button" class="m3-item drow" @click="search"><Icon name="search" :size="22" /><span class="l">{{ $t('skinMaterial.search') }}</span></button>
          <hr>
          <button type="button" class="m3-item drow" :class="{ on: editing }" :aria-pressed="editing" @click="editing = !editing">
            <Icon name="pin" :size="22" /><span class="l">{{ editing ? $t('skinMaterial.done') : $t('skinMaterial.editTabs') }}</span>
            <span v-if="editing" class="dcount">{{ `${keys.length}/${max}` }}</span>
          </button>
          <div v-if="editing" class="dhint">{{ $t('skinMaterial.pinHint', { max }) }}</div>
          <template v-if="editing">
            <button v-for="n in nav" :key="'e' + n.to" type="button" role="checkbox" :aria-checked="isPinned(n.to)" class="m3-item drow" :class="{ dim: pinsFull && !isPinned(n.to) }" @click="toggle(n.to)">
              <Icon :name="n.icon" :size="22" /><span class="l">{{ n.label }}</span>
              <span class="cbx" :class="{ on: isPinned(n.to) }"><svg v-if="isPinned(n.to)" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="m5 12 5 5 9-10" stroke="currentColor" stroke-width="3" fill="none" /></svg></span>
            </button>
          </template>
          <template v-else>
            <NuxtLink v-for="n in nav" :key="n.to" :to="n.to" class="m3-item drow" :class="{ on: n.to === path }" @click="drawer = false">
              <Icon :name="n.icon" :size="22" /><span class="l">{{ n.label }}</span>
              <span v-if="badge(n.to)" class="dbdg">{{ badge(n.to) }}</span>
              <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
            </NuxtLink>
          </template>
        </aside>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* shared bits */
.m3-icon { display: grid; place-items: center; width: 48px; height: 48px; flex: none; padding: 0; border: 0; border-radius: 50%; background: none; color: var(--muted); cursor: pointer; -webkit-tap-highlight-color: transparent; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ok); flex: none; }
.dot.warn { background: var(--warn); } .dot.bad { background: var(--bad); }
.cm { position: absolute; top: 2px; left: calc(50% + 8px); width: 8px; height: 8px; border-radius: 50%; background: var(--accent); }
.cm.busy { animation: m3pulse 1.4s ease-in-out infinite; }
.cm.input { background: var(--warn); }
@keyframes m3pulse { 50% { opacity: .35; transform: scale(.7); } }
.bdg { position: absolute; top: -3px; left: calc(50% + 4px); min-width: 16px; height: 16px; padding: 0 4px; border-radius: 8px; background: var(--bad); color: color-mix(in srgb, var(--bad) 18%, black); font-size: 11px; font-weight: 500; line-height: 16px; text-align: center; }

/* top app bar (phone) */
.m3-top { display: none; }
.m3-bar { display: none; }
.m3-title { flex: 1; min-width: 0; font-size: 22px; line-height: 28px; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; opacity: 0; transform: translateY(6px); transition: opacity .2s, transform .25s cubic-bezier(.2, 0, 0, 1); }
.m3-title.show { opacity: 1; transform: none; }

/* destinations (bar + rail) */
.m3-dest { position: relative; display: flex; flex-direction: column; align-items: center; gap: 4px; min-width: 0; color: var(--muted); text-decoration: none; background: none; border: 0; font: inherit; cursor: pointer; -webkit-tap-highlight-color: transparent; }
.m3-dest:hover { text-decoration: none; color: var(--text); }
.ind { position: relative; display: grid; place-items: center; width: 64px; height: 32px; }
.pill { position: absolute; inset: 0; border-radius: 16px; background: var(--m3-sec); opacity: 0; transform: scaleX(.32); transition: transform .38s cubic-bezier(.2, 0, 0, 1), opacity .16s; }
.m3-dest.on .pill { opacity: 1; transform: scaleX(1); }
.ic { position: relative; transition: transform .25s cubic-bezier(.2, 0, 0, 1); }
.m3-dest.on .ic { color: var(--m3-on-sec); }
.lbl { max-width: 100%; font-size: 12px; font-weight: 500; letter-spacing: .4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.m3-dest.on .lbl { color: var(--text); font-weight: 700; }

/* navigation rail (desktop) */
.m3-rail { position: fixed; z-index: 60; top: 0; bottom: 0; left: 0; width: 88px; display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 16px 0 12px; background: var(--bg); }
.m3-fab { display: grid; place-items: center; width: 56px; height: 56px; flex: none; margin-bottom: 8px; border: 0; border-radius: 16px; background: var(--m3-pri-c); color: var(--m3-on-pri-c); cursor: pointer; box-shadow: 0 1px 3px rgba(0, 0, 0, .3), 0 4px 8px 3px rgba(0, 0, 0, .15); transition: box-shadow .2s, border-radius .25s; }
.m3-fab:hover { box-shadow: 0 2px 3px rgba(0, 0, 0, .3), 0 6px 10px 4px rgba(0, 0, 0, .15); }
.rail-list { flex: 1; min-height: 0; width: 100%; display: flex; flex-direction: column; align-items: center; gap: 10px; overflow-y: auto; scrollbar-width: none; padding: 4px 0; }
.rail-list::-webkit-scrollbar { display: none; }
.rail-list .m3-dest { width: 80px; }
.rail-list .ind { width: 56px; }
.rail-foot { display: flex; flex-direction: column; align-items: center; gap: 8px; max-width: 84px; }
.rail-foot :deep(.jt) { padding: 6px 8px; font-size: 11.5px; }
.st { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--faint); white-space: nowrap; }

/* drawer */
.m3-scrim { position: fixed; inset: 0; z-index: 70; background: rgba(0, 0, 0, .4); }
.m3-drawer { position: absolute; top: 0; bottom: 0; left: 0; width: min(360px, 86vw); display: flex; flex-direction: column; gap: 2px; padding: calc(12px + env(safe-area-inset-top)) 12px calc(16px + env(safe-area-inset-bottom)); overflow-y: auto; background: var(--panel); border-radius: 0 16px 16px 0; box-shadow: 0 8px 24px rgba(0, 0, 0, .4); }
.dh { display: flex; align-items: center; justify-content: space-between; padding: 0 0 0 16px; }
.brand { font-size: 14px; font-weight: 500; color: var(--muted); letter-spacing: .1px; }
.dstate { display: flex; align-items: center; gap: 8px; padding: 0 16px 8px; font-size: 12px; color: var(--faint); }
.drow { display: flex; flex-direction: row; align-items: center; gap: 12px; min-height: 56px; padding: 0 24px 0 16px; border: 0; border-radius: 28px; background: none; color: var(--muted); font: inherit; font-size: 14px; font-weight: 500; letter-spacing: .1px; text-align: left; text-decoration: none; cursor: pointer; flex: none; }
.drow:hover { text-decoration: none; background: color-mix(in srgb, var(--text) 8%, transparent); }
.drow.on { background: var(--m3-sec); color: var(--m3-on-sec); }
.drow .l { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.drow .cm { position: static; }
.drow.dim { opacity: .38; }
.dcount { font-size: 12px; font-weight: 600; }
.dhint { padding: 0 16px 6px 52px; font-size: 12px; color: var(--faint); }
.cbx { display: grid; place-items: center; width: 18px; height: 18px; flex: none; border: 2px solid var(--muted); border-radius: 2px; }
.cbx.on { background: var(--accent); border-color: var(--accent); color: var(--m3-on-pri); }
.dbdg { font-size: 12px; font-weight: 600; color: var(--bad); }
hr { border: 0; border-top: 1px solid var(--line); margin: 6px 16px; flex: none; }
.m3d-enter-active, .m3d-leave-active { transition: opacity .3s; }
.m3d-enter-active .m3-drawer { transition: transform .4s cubic-bezier(.05, .7, .1, 1); }
.m3d-leave-active .m3-drawer { transition: transform .2s cubic-bezier(.3, 0, .8, .15); }
.m3d-enter-from, .m3d-leave-to { opacity: 0; }
.m3d-enter-from .m3-drawer, .m3d-leave-to .m3-drawer { transform: translateX(-100%); }

@media (max-width: 640px) {
  .m3-rail { display: none; }
  .m3-top { position: fixed; z-index: 60; top: 0; left: 0; right: 0; display: flex; align-items: center; gap: 4px; height: calc(64px + env(safe-area-inset-top)); padding: env(safe-area-inset-top) 4px 0; background: var(--bg); transition: background-color .25s; }
  .m3-top.scrolled { background: var(--panel); }
  .m3-top.top { background: transparent; }
  .m3-top :deep(.jt) { margin-right: 2px; }
  .m3-title { padding-left: 16px; }
  .m3-bar { position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; display: flex; height: calc(80px + env(safe-area-inset-bottom)); padding: 12px 0 calc(16px + env(safe-area-inset-bottom)); background: var(--panel); }
  .m3-bar .m3-dest { flex: 1; }
  .m3-bar .lbl { max-width: 84px; }
}
@media (prefers-reduced-motion: reduce) {
  .pill, .m3-title, .ic, .m3d-enter-active .m3-drawer, .m3d-leave-active .m3-drawer { transition: none !important; }
  .cm.busy { animation: none; }
}
</style>

<style>
/* the skin's global part: tonal roles from the tokens, room for the bars, ripples, controls, page transition */
html.skin-material {
  --m3-sec: color-mix(in srgb, var(--accent) 26%, var(--panel));
  --m3-on-sec: color-mix(in srgb, var(--accent) 35%, var(--text));
  --m3-pri-c: color-mix(in srgb, var(--accent) 34%, var(--bg));
  --m3-on-pri-c: color-mix(in srgb, var(--accent) 45%, var(--text));
  --m3-on-pri: color-mix(in srgb, var(--accent) 22%, black);
}
/* see-through body: the tonal Backdrop (z-index -1) paints the surface */
html.skin-material body { background: transparent; }
/* M3 symbols: 2 px strokes with a tonal fill */
html.skin-material svg.icon { stroke-width: 2; fill: color-mix(in srgb, currentColor 14%, transparent); }
html.skin-material .m3-dest.on svg.icon { fill: color-mix(in srgb, currentColor 30%, transparent); }
html.skin-material body { font-family: Roboto, "Google Sans", "Google Sans Text", system-ui, sans-serif; }
@media (min-width: 641px) {
  html.skin-material .shell.skinned { padding-left: 88px; }
}
@media (max-width: 640px) {
  html.skin-material .shell.skinned { --tabbar: calc(80px + env(safe-area-inset-bottom)); }
  html.skin-material .m3-nav:not(.full) ~ main.wrap { padding-top: calc(68px + env(safe-area-inset-top)); }
}
html.skin-material .m3-ripple-box { position: fixed; z-index: 9999; overflow: hidden; pointer-events: none; animation: m3-rip-fade .7s linear forwards; }
html.skin-material .m3-ripple-dot { position: absolute; border-radius: 50%; opacity: .14; transform: scale(0); animation: m3-rip .45s cubic-bezier(.2, 0, 0, 1) forwards; }
@keyframes m3-rip { to { transform: scale(1); } }
@keyframes m3-rip-fade { 0%, 55% { opacity: 1; } 100% { opacity: 0; } }

/* controls, M3 shapes (only shapes and tonal fills: sizes stay the core's) */
html.skin-material .btn { border-radius: 20px; font-weight: 500; letter-spacing: .1px; }
html.skin-material .btn.icon { border-radius: 50%; }
html.skin-material .btn.primary { background: var(--accent); border-color: var(--accent); color: var(--m3-on-pri); }
html.skin-material .btn:not(.primary):not(.ghost) { background: var(--panel-2); border-color: var(--line); }
html.skin-material .btn.ghost:not(.icon):not(.armed) { color: var(--accent); }
html.skin-material .chip { border-radius: 8px; border-color: var(--line); }
html.skin-material .chip.on { background: var(--m3-sec); color: var(--m3-on-sec); border-color: transparent; }
html.skin-material .seg { border-radius: 20px; border-color: var(--line-2); }
html.skin-material .seg > button.on { background: var(--m3-sec); color: var(--m3-on-sec); }
html.skin-material .pill { border-radius: 8px; }
html.skin-material .sec { color: var(--accent); font-size: 14px; font-weight: 500; letter-spacing: .1px; }
html.skin-material :is(input:not([type="checkbox"]):not([type="radio"]):not([type="range"]), select, textarea) { border-radius: 4px; }
html.skin-material :is(input, select, textarea):focus-visible { outline: 2px solid var(--accent); outline-offset: -1px; }

/* page change: shared axis X (out to the left, in from the right) */
html.skin-material .skin-material-leave-active { transition: opacity 90ms cubic-bezier(.4, 0, 1, 1), transform 90ms cubic-bezier(.4, 0, 1, 1); }
html.skin-material .skin-material-enter-active { transition: opacity 210ms cubic-bezier(0, 0, .2, 1), transform 300ms cubic-bezier(.2, 0, 0, 1); }
html.skin-material .skin-material-enter-from { opacity: 0; transform: translateX(30px); }
html.skin-material .skin-material-leave-to { opacity: 0; transform: translateX(-30px); }
/* phone: fade only. A sideways slide widens the page for a moment, which made the fixed bars and the browser toolbar jump */
@media (max-width: 640px) {
  html.skin-material main.wrap { overflow-x: clip; }
  html.skin-material .skin-material-enter-from, html.skin-material .skin-material-leave-to { transform: none; }
}
@media (prefers-reduced-motion: reduce) {
  html.skin-material .skin-material-enter-active, html.skin-material .skin-material-leave-active { transition: none; }
  html.skin-material .skin-material-enter-from, html.skin-material .skin-material-leave-to { transform: none; }
  html.skin-material .m3-ripple-box { display: none; }
}
</style>
