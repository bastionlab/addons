<script setup lang="ts">
/**
 * Liquid Glass navigation. Desktop: a floating glass dock centred at the bottom with macOS-style magnification
 * (the item under the pointer and its neighbours grow), the active page's label always shown + a dot under it,
 * labels of hovered items on top. Phone (and desktops too narrow for every page): a floating capsule tab bar with
 * the viewer's pinned pages (useNavPins) + "More", which springs up a glass sheet with every page ("Edit" there
 * picks the pinned ones). On full-screen pages (/chat)
 * the desktop dock hides itself to a small handle and comes back on hover or tap.
 */
const props = withDefaults(defineProps<{
  nav?: { to: string, icon: string, label: string }[], path?: string
  badge?: (to: string) => number, mark?: (to: string) => string
  state?: string, stateText?: string, up?: string, full?: boolean
}>(), { nav: () => [], path: '/', badge: () => 0, mark: () => '', state: 'ok', stateText: '', up: '', full: false })
const emit = defineEmits<{ search: [] }>()

const nav = computed(() => props.nav ?? [])
const pins = useNavPins(() => nav.value)
const { editing } = pins
const tabs = pins.pinned
const here = computed(() => nav.value.find(n => n.to === props.path))
const offTab = computed(() => (here.value && !tabs.value.some(t => t.to === here.value!.to) ? here.value : null))
const sheet = ref(false)
const slots = computed(() => tabs.value.length + 1)
const hl = computed(() => {
  if (sheet.value || offTab.value) return tabs.value.length
  return tabs.value.findIndex(t => t.to === props.path)
})
const restBadge = computed(() => nav.value.filter(n => !tabs.value.some(t => t.to === n.to)).reduce((s, n) => s + (props.badge(n.to) || 0), 0))
const restMark = computed(() => nav.value.filter(n => !tabs.value.some(t => t.to === n.to)).map(n => props.mark(n.to)).find(Boolean) ?? '')

watch(() => props.path, () => (sheet.value = false))
watch(sheet, v => { if (!v) editing.value = false })
function go(to: string) { if (editing.value) { pins.toggle(to); return } sheet.value = false; navigateTo(to) }
function search() { sheet.value = false; emit('search') }

/** a stable hue per page for the sheet's app icons */
function hue(s: string) { let h = 0; for (const c of s) h = (h * 31 + c.charCodeAt(0)) % 360; return h }
const tileBg = (to: string) => { const h = hue(to); return { background: `linear-gradient(145deg, hsl(${h} 85% 64%), hsl(${(h + 40) % 360} 75% 46%))` } }

// dock magnification: base centres measured when the pointer enters, scale falls off with distance
const dockEl = ref<HTMLElement | null>(null)
const mx = ref<number | null>(null)
let centres: number[] = []
function enter(e: PointerEvent) {
  if (e.pointerType === 'touch' || reduced) return
  const els = dockEl.value?.querySelectorAll<HTMLElement>('.di') ?? []
  centres = Array.from(els, el => { const r = el.getBoundingClientRect(); return r.left + r.width / 2 })
  mx.value = e.clientX
}
function move(e: PointerEvent) { if (e.pointerType !== 'touch' && centres.length && !reduced) mx.value = e.clientX }
function leave() { mx.value = null; centres = [] }
function scale(i: number) {
  if (mx.value == null || centres[i] == null) return 1
  const d = Math.abs(mx.value - centres[i]!) / 130
  return 1 + 0.55 * Math.max(0, 1 - d * d)
}

// too many pages for a dock on this screen → the capsule bar instead
const W = ref(0)
const crowded = computed(() => W.value > 640 && nav.value.length * 54 + 200 > W.value - 40)
const peek = ref(false)
let reduced = false
const onResize = () => (W.value = window.innerWidth)
const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') sheet.value = false }
onMounted(() => {
  reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  onResize()
  window.addEventListener('resize', onResize, { passive: true })
  window.addEventListener('keydown', onKey)
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  window.removeEventListener('keydown', onKey)
})
watch(() => props.full, () => (peek.value = false))
</script>

<template>
  <div class="glass-nav" :class="{ crowded, full }">
    <!-- desktop dock -->
    <div class="dock-zone" :class="{ hidden: full && !peek }" @pointerenter="peek = true" @pointerleave="peek = false">
      <button v-if="full" type="button" class="handle" :aria-label="$t('skinGlass.allPages')" @click="peek = !peek"><i /></button>
      <nav ref="dockEl" class="dock" @pointerenter="enter" @pointermove="move" @pointerleave="leave">
        <NuxtLink v-for="(n, i) in nav" :key="n.to" :to="n.to" class="di" :class="{ on: n.to === path }" :style="{ '--s': scale(i) }" :aria-label="n.label">
          <span class="ic"><Icon :name="n.icon" :size="22" /></span>
          <span class="lbl">{{ n.label }}</span>
          <span v-if="badge(n.to)" class="bdg">{{ badge(n.to) }}</span>
          <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
        </NuxtLink>
        <span class="sep" />
        <button type="button" class="di tool" :aria-label="$t('skinGlass.search')" @click="emit('search')">
          <span class="ic"><Icon name="search" :size="20" /></span>
          <span class="lbl">{{ $t('skinGlass.search') }}</span>
        </button>
        <span class="jobs"><JobsButton /></span>
        <span class="live" :class="state"><i class="dot" /><span>{{ up }}</span><span class="st">{{ stateText }}</span></span>
      </nav>
    </div>

    <!-- phone: top-right cluster (jobs + search); full-screen pages (/chat) keep their own header row clear, both live in More -->
    <div v-if="!full" class="corner">
      <JobsButton />
      <button type="button" class="orb" :aria-label="$t('skinGlass.search')" @click="emit('search')"><Icon name="search" :size="18" /></button>
    </div>

    <!-- phone capsule tab bar -->
    <nav class="cap" data-skin-bar :class="{ lifted: sheet }" :style="{ '--n': slots }">
      <span v-if="hl >= 0" class="hl" :style="{ transform: `translateX(${hl * 100}%)` }" />
      <NuxtLink v-for="n in tabs" :key="n.to" :to="n.to" class="ct" :class="{ on: n.to === path && !sheet }">
        <Icon :name="n.icon" :size="22" /><span class="cl">{{ n.label }}</span>
        <span v-if="badge(n.to)" class="bdg">{{ badge(n.to) }}</span>
        <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
      </NuxtLink>
      <button type="button" class="ct" :class="{ on: sheet || offTab }" :aria-expanded="sheet" @click="sheet = !sheet">
        <Icon :name="offTab && !sheet ? offTab.icon : 'grid'" :size="22" />
        <span class="cl">{{ offTab && !sheet ? offTab.label : $t('skinGlass.more') }}</span>
        <span v-if="restBadge" class="bdg">{{ restBadge }}</span>
        <span v-else-if="restMark" class="cm" :class="restMark" />
        <span v-else-if="state !== 'ok'" class="cm" :class="state === 'bad' ? 'bad' : 'input'" />
      </button>
    </nav>

    <Transition name="gsheet">
      <div v-if="sheet" class="scrim" @click.self="sheet = false">
        <div class="sheet" role="dialog" :aria-label="$t('skinGlass.allPages')">
          <div class="grab" />
          <div class="sh-head">
            <b>{{ $t('skinGlass.allPages') }}</b>
            <span class="live" :class="state"><i class="dot" /><span>{{ up }} · {{ stateText }}</span></span>
            <button type="button" class="pill" :class="{ on: editing }" :aria-pressed="editing" @click="editing = !editing">{{ editing ? $t('skinGlass.done') : $t('skinGlass.edit') }}</button>
            <button type="button" class="orb" :aria-label="$t('skinGlass.search')" @click="search"><Icon name="search" :size="17" /></button>
            <button type="button" class="orb" :aria-label="$t('skinGlass.close')" @click="sheet = false"><Icon name="stop" :size="15" /></button>
          </div>
          <div v-if="editing" class="hint">{{ $t('skinGlass.pinHint', { n: pins.keys.value.length, max: pins.max }) }}</div>
          <div class="sh-jobs"><JobsButton /></div>
          <div class="apps">
            <button v-for="(n, i) in nav" :key="n.to" type="button" class="app"
              :class="{ on: !editing && n.to === path, pinned: editing && pins.isPinned(n.to), dim: editing && pins.full.value && !pins.isPinned(n.to) }"
              :aria-pressed="editing ? pins.isPinned(n.to) : undefined" :style="{ '--d': `${Math.min(i, 16) * 18}ms` }" @click="go(n.to)">
              <span class="tile" :style="tileBg(n.to)"><Icon :name="n.icon" :size="24" /></span>
              <span class="al">{{ n.label }}</span>
              <span v-if="editing && pins.isPinned(n.to)" class="pinm"><Icon name="check" :size="14" /></span>
              <span v-else-if="badge(n.to)" class="bdg">{{ badge(n.to) }}</span>
              <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* ---------- shared bits ---------- */
.bdg { position: absolute; top: -3px; right: -3px; min-width: 18px; height: 18px; padding: 0 5px; border-radius: 999px; background: var(--bad); color: var(--text); font-size: 11px; font-weight: 700; line-height: 18px; text-align: center; box-shadow: 0 2px 6px rgba(0, 0, 0, .35); }
.cm { position: absolute; top: 2px; right: 2px; width: 9px; height: 9px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 0 2px rgba(10, 12, 30, .6); }
.cm.busy { animation: gpulse 1.4s ease-in-out infinite; }
.cm.input { background: var(--warn); }
.cm.bad { background: var(--bad); }
@keyframes gpulse { 50% { opacity: .35; transform: scale(.7); } }
.live { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--muted); white-space: nowrap; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 10px var(--ok); }
.live.warn .dot { background: var(--warn); box-shadow: 0 0 10px var(--warn); }
.live.bad .dot { background: var(--bad); box-shadow: 0 0 10px var(--bad); }
.orb { display: grid; place-items: center; width: 38px; height: 38px; border-radius: 50%; color: var(--text); cursor: pointer; background: rgba(255, 255, 255, .1); border: 1px solid rgba(255, 255, 255, .16); box-shadow: inset 0 1px 0 rgba(255, 255, 255, .2), 0 6px 20px rgba(0, 0, 0, .3); backdrop-filter: blur(20px) saturate(180%); -webkit-backdrop-filter: blur(20px) saturate(180%); }
.orb:active { transform: scale(.92); }
.glass-nav :deep(.jt) { background: rgba(255, 255, 255, .1); border-color: rgba(255, 255, 255, .16); color: var(--text); backdrop-filter: blur(20px) saturate(180%); -webkit-backdrop-filter: blur(20px) saturate(180%); }

/* ---------- desktop dock ---------- */
.dock-zone { position: fixed; z-index: 60; left: 50%; bottom: 14px; transform: translateX(-50%); transition: transform var(--dur-slow) var(--ease-spring); }
.dock-zone.hidden { transform: translate(-50%, calc(100% + 4px)); }
.handle { position: absolute; left: 50%; bottom: calc(100% + 6px); transform: translateX(-50%); display: grid; place-items: center; width: 72px; height: 32px; padding: 0; border: 0; background: none; cursor: pointer; }
.handle i { width: 46px; height: 5px; border-radius: 99px; background: rgba(255, 255, 255, .45); box-shadow: 0 1px 8px rgba(0, 0, 0, .4); }
.dock-zone.hidden .handle { bottom: calc(100% + 10px); }
.dock-zone:not(.hidden) .handle { opacity: 0; pointer-events: none; }
.dock {
  position: relative; display: flex; align-items: flex-end; gap: 6px; padding: 8px 10px; border-radius: 26px;
  background: linear-gradient(180deg, rgba(255, 255, 255, .14), rgba(255, 255, 255, .06));
  border: 1px solid rgba(255, 255, 255, .18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .28), inset 0 -1px 0 rgba(255, 255, 255, .05), 0 20px 50px rgba(0, 0, 0, .5);
  backdrop-filter: blur(28px) saturate(190%); -webkit-backdrop-filter: blur(28px) saturate(190%);
}
.di {
  --b: 46px; position: relative; flex: none; display: grid; place-items: center;
  width: calc(var(--b) * var(--s, 1)); height: calc(var(--b) * var(--s, 1));
  border-radius: calc(14px * var(--s, 1)); color: var(--text); text-decoration: none; cursor: pointer; padding: 0; font: inherit;
  background: linear-gradient(160deg, rgba(255, 255, 255, .18), rgba(255, 255, 255, .04));
  border: 1px solid rgba(255, 255, 255, .14); box-shadow: inset 0 1px 0 rgba(255, 255, 255, .25), 0 4px 12px rgba(0, 0, 0, .25);
  transition: width .16s ease-out, height .16s ease-out, border-radius .16s ease-out, background .2s;
}
.di:hover { text-decoration: none; }
.di .ic { display: grid; place-items: center; width: 100%; height: 100%; line-height: 0; }
.di .icon { width: 52%; height: 52%; }
.di.on { background: linear-gradient(160deg, color-mix(in srgb, var(--accent) 55%, rgba(255, 255, 255, .2)), color-mix(in srgb, var(--accent) 22%, transparent)); color: var(--text); }
.di.on::after { content: ''; position: absolute; bottom: -7px; left: 50%; width: 5px; height: 5px; margin-left: -2.5px; border-radius: 50%; background: var(--text); box-shadow: 0 0 8px var(--text); }
.lbl {
  position: absolute; bottom: calc(100% + 12px); left: 50%; transform: translate(-50%, 4px) scale(.94); opacity: 0;
  padding: 4px 11px; border-radius: 10px; white-space: nowrap; font-size: 12.5px; font-weight: 500; color: var(--text); pointer-events: none;
  background: rgba(20, 24, 44, .78); border: 1px solid rgba(255, 255, 255, .14); box-shadow: 0 6px 18px rgba(0, 0, 0, .35);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  transition: opacity .18s, transform .3s cubic-bezier(.34, 1.56, .64, 1);
}
.di.on .lbl { opacity: 1; transform: translate(-50%, 0) scale(1); }
.di:hover .lbl, .di:focus-visible .lbl { opacity: 1; transform: translate(-50%, 0) scale(1); z-index: 3; background: rgba(40, 46, 80, .92); }
.dock:has(.di:not(.on):hover) .di.on .lbl { opacity: .45; }
.sep { align-self: stretch; width: 1px; margin: 6px 2px; background: rgba(255, 255, 255, .2); }
.tool { background: rgba(255, 255, 255, .06); }
.jobs:empty { display: none; }
.jobs { align-self: center; }
.dock .live { align-self: center; padding: 0 4px 0 2px; }
.dock .live .st { display: none; }
.dock .live:not(.ok) .st { display: inline; }

/* ---------- phone pieces (hidden on desktop) ---------- */
.corner, .cap { display: none; }
.cap {
  position: fixed; z-index: 60; left: 12px; right: 12px; bottom: calc(10px + env(safe-area-inset-bottom)); height: 64px;
  padding: 6px; border-radius: 999px;
  background: linear-gradient(180deg, rgba(255, 255, 255, .15), rgba(255, 255, 255, .06));
  border: 1px solid rgba(255, 255, 255, .18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .3), 0 18px 40px rgba(0, 0, 0, .55);
  backdrop-filter: blur(26px) saturate(190%); -webkit-backdrop-filter: blur(26px) saturate(190%);
}
.hl {
  position: absolute; top: 6px; bottom: 6px; left: 6px; width: calc((100% - 12px) / var(--n)); border-radius: 999px;
  background: linear-gradient(180deg, rgba(255, 255, 255, .24), rgba(255, 255, 255, .1));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .35), 0 4px 14px rgba(0, 0, 0, .25);
  transition: transform var(--dur-slow) var(--ease-spring);
}
.ct {
  position: relative; flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px;
  color: var(--muted); font: inherit; font-size: 10.5px; font-weight: 500; background: none; border: 0; padding: 0; cursor: pointer;
  text-decoration: none; -webkit-tap-highlight-color: transparent; transition: color .2s, transform .3s cubic-bezier(.34, 1.56, .64, 1);
}
.ct:hover { text-decoration: none; }
.ct:active { transform: scale(.9); }
.ct.on { color: var(--text); }
.ct.on .icon { filter: drop-shadow(0 0 6px color-mix(in srgb, var(--accent) 70%, transparent)); color: var(--accent); }
.cl { max-width: 100%; padding: 0 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ct .bdg { top: 2px; right: calc(50% - 22px); }
.ct .cm { top: 6px; right: calc(50% - 16px); }
.corner { position: fixed; z-index: 58; top: calc(env(safe-area-inset-top, 0px) + 10px); right: 12px; align-items: center; gap: 8px; }

/* ---------- More sheet ---------- */
.scrim { position: fixed; inset: 0; z-index: 70; background: rgba(4, 6, 16, .45); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); }
.sheet {
  position: absolute; left: 10px; right: 10px; bottom: calc(10px + env(safe-area-inset-bottom)); max-height: calc(100dvh - 60px); overflow-y: auto;
  max-width: 560px; margin: 0 auto; padding: 8px 16px 18px; border-radius: 32px;
  background: linear-gradient(180deg, rgba(40, 46, 82, .72), rgba(18, 22, 44, .78));
  border: 1px solid rgba(255, 255, 255, .18); box-shadow: inset 0 1px 0 rgba(255, 255, 255, .3), 0 30px 80px rgba(0, 0, 0, .6);
  backdrop-filter: blur(36px) saturate(200%); -webkit-backdrop-filter: blur(36px) saturate(200%);
}
.grab { width: 40px; height: 5px; border-radius: 99px; margin: 2px auto 10px; background: rgba(255, 255, 255, .3); }
.sh-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.sh-head b { font-size: 22px; font-weight: 700; letter-spacing: -.02em; }
.sh-head .live { margin-left: auto; min-width: 0; overflow: hidden; }
.sh-head .live span { overflow: hidden; text-overflow: ellipsis; }
.sh-jobs:empty { display: none; }
.sh-jobs { margin: -4px 0 10px; }
.apps { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px 6px; }
.app { position: relative; display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 0; background: none; border: 0; color: var(--muted); font: inherit; font-size: 11.5px; cursor: pointer; -webkit-tap-highlight-color: transparent; }
.tile { display: grid; place-items: center; width: 58px; height: 58px; border-radius: 16px; color: rgba(255, 255, 255, .96); box-shadow: inset 0 1px 0 rgba(255, 255, 255, .45), inset 0 -2px 6px rgba(0, 0, 0, .18), 0 8px 18px rgba(0, 0, 0, .35); transition: transform .3s cubic-bezier(.34, 1.56, .64, 1); }
.app:active .tile { transform: scale(.9); }
.app.on { color: var(--text); font-weight: 600; }
.app.on .tile { outline: 2px solid rgba(255, 255, 255, .85); outline-offset: 3px; }
.al { max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.app .bdg { top: -4px; right: calc(50% - 34px); }
.app .cm { top: -2px; right: calc(50% - 30px); }
.pill { min-height: 32px; padding: 0 14px; border-radius: 999px; color: var(--text); font: inherit; font-size: 13px; font-weight: 600; cursor: pointer; background: rgba(255, 255, 255, .1); border: 1px solid rgba(255, 255, 255, .16); box-shadow: inset 0 1px 0 rgba(255, 255, 255, .2); }
.pill.on { background: var(--accent); border-color: transparent; }
.hint { margin: -4px 0 10px; font-size: 12.5px; color: var(--muted); }
.app.pinned .tile { outline: 2px solid rgba(255, 255, 255, .85); outline-offset: 3px; }
.app.dim { opacity: .4; }
.pinm { position: absolute; top: -4px; right: calc(50% - 34px); display: grid; place-items: center; width: 20px; height: 20px; border-radius: 50%; color: var(--text); background: var(--accent); box-shadow: 0 2px 6px rgba(0, 0, 0, .35); }

.gsheet-enter-active { transition: opacity .25s; }
.gsheet-leave-active { transition: opacity .22s; }
.gsheet-enter-active .sheet { transition: transform var(--dur-slow) var(--ease-spring), opacity var(--dur); }
.gsheet-leave-active .sheet { transition: transform .25s ease-in, opacity .22s; }
.gsheet-enter-from, .gsheet-leave-to { opacity: 0; }
.gsheet-enter-from .sheet, .gsheet-leave-to .sheet { transform: translateY(70%) scale(.94); opacity: 0; }
.gsheet-enter-active .app { animation: gapp .45s cubic-bezier(.34, 1.56, .64, 1) both; animation-delay: var(--d); }
@keyframes gapp { from { opacity: 0; transform: translateY(14px) scale(.8); } }

@media (max-width: 640px) {
  .dock-zone { display: none; }
  .cap { display: flex; }
  .corner { display: flex; }
  html.kb .cap { display: none; }
}
.crowded .dock-zone { display: none; }
.crowded .cap { display: flex; left: 50%; right: auto; width: min(460px, calc(100vw - 24px)); transform: translateX(-50%); }
.crowded .corner { display: flex; }

@media (prefers-reduced-motion: reduce) {
  .dock-zone, .di, .lbl, .hl, .ct, .tile { transition: none; }
  .cm.busy, .gsheet-enter-active .app { animation: none; }
  .gsheet-enter-active .sheet, .gsheet-leave-active .sheet { transition: opacity .15s; }
  .gsheet-enter-from .sheet, .gsheet-leave-to .sheet { transform: none; }
}
/* phone budget (SKINS.md): no backdrop-filter on large layers, a denser translucent fill instead */
@media (max-width: 640px), (pointer: coarse) {
  .orb, .glass-nav :deep(.jt) { backdrop-filter: none; -webkit-backdrop-filter: none; background: color-mix(in srgb, var(--panel) 92%, transparent); }
  .cap { backdrop-filter: none; -webkit-backdrop-filter: none; background: linear-gradient(180deg, rgba(255, 255, 255, .15), rgba(255, 255, 255, .06)), color-mix(in srgb, var(--panel) 94%, transparent); }
  .sheet { backdrop-filter: none; -webkit-backdrop-filter: none; background: color-mix(in srgb, var(--panel) 96%, transparent); }
  .scrim { backdrop-filter: none; -webkit-backdrop-filter: none; background: rgba(4, 6, 16, .6); }
}
</style>

<style>
/* room for the dock / capsule; only while this skin is on */
html.skin-glass .shell.skinned { --tabbar: calc(84px + env(safe-area-inset-bottom)); }
html.skin-glass main.wrap { padding-bottom: calc(110px + env(safe-area-inset-bottom)); }
@media (max-width: 640px) { html.skin-glass main.wrap { padding-bottom: calc(var(--tabbar) + 24px); } }
/* the body is see-through so the aurora Backdrop (z-index -1) shows behind the page instead of under an opaque body */
html.skin-glass body { background: transparent; }
/* the phone's top-right orbs (jobs + search) are fixed: the page starts under them and its tab row sticks below them,
   so they never sit on a page's own buttons */
@media (max-width: 640px) {
  html.skin-glass .glass-nav:not(.full) ~ main.wrap { padding-top: calc(env(safe-area-inset-top, 0px) + 56px); }
  html.skin-glass { --ptabs-top: calc(env(safe-area-inset-top, 0px) + 48px); }
}
html.skin-glass .glass-nav.crowded:not(.full) ~ main.wrap { padding-top: calc(env(safe-area-inset-top, 0px) + 56px); }
/* thin, soft icons like the system glyphs on glass */
html.skin-glass svg.icon { stroke-width: 1.5; }
html.skin-glass body { font-family: -apple-system, "SF Pro Display", "SF Pro Text", system-ui, "Segoe UI", Roboto, sans-serif; }
</style>
