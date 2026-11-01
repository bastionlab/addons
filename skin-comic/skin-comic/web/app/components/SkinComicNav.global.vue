<script setup lang="ts">
/**
 * Comic Book navigation. Desktop: a masthead ("BASTION COMICS #<day of year>") with every page as an issue tab
 * under it. Phone: a compact masthead and a bottom bar of speech bubbles: the viewer's pinned pages (useNavPins),
 * the open page if it isn't pinned, and "more" (every page + "edit tabs"). Full-screen pages (/chat) on desktop get a
 * floating burst button with the pages.
 * Also owns the onomatopoeia: tapping any .btn pops a POW!/ZAP!/BAM!/WHAM! starburst at the pointer.
 */
const props = withDefaults(defineProps<{
  nav?: { to: string, icon: string, label: string }[], path?: string
  badge?: (to: string) => number, mark?: (to: string) => string
  state?: string, stateText?: string, up?: string, full?: boolean
}>(), { nav: () => [], path: '/', badge: () => 0, mark: () => '', state: 'ok', stateText: '', up: '', full: false })
const emit = defineEmits<{ search: [] }>()
const { t } = useI18n()

const now = new Date()
const doy = Math.floor((now.getTime() - new Date(now.getFullYear(), 0, 0).getTime()) / 86400000)
const pop = ref(false)
watch(() => props.path, () => { pop.value = false; nextTick(centre) })
// phone bar: pinned pages + the open one if unpinned + "more"; "more" can edit the pins
const pins = useNavPins(() => props.nav)
const { editing } = pins
const offTab = computed(() => props.nav.find(n => n.to === props.path && !pins.isPinned(n.to)) ?? null)
const moreBadge = computed(() => props.nav.filter(n => !pins.isPinned(n.to)).reduce((s, n) => s + props.badge(n.to), 0))
watch(pop, v => { if (!v) editing.value = false })
function pick(to: string) { if (editing.value) pins.toggle(to); else { pop.value = false; if (to !== props.path) navigateTo(to) } }

// keep the current bubble in view on the phone bar
const bar = ref<HTMLElement | null>(null)
function centre() {
  const b = bar.value
  const on = b?.querySelector<HTMLElement>('.bub.on')
  if (!b || !on) return
  b.scrollTo({ left: on.offsetLeft - (b.clientWidth - on.offsetWidth) / 2, behavior: 'smooth' })
}

// onomatopoeia bursts on every button tap, only while this skin is mounted
type Burst = { id: number, x: number, y: number, word: string, fill: string, rot: number }
const bursts = ref<Burst[]>([])
const WORDS = ['pow', 'zap', 'bam', 'wham']
const FILLS = ['#ffd83d', '#ff5a5f', '#4fc3ff', '#ffffff']
let seq = 0
let reduced = false
const timers = new Set<ReturnType<typeof setTimeout>>()
function onDown(e: PointerEvent) {
  if (reduced) return
  const el = (e.target as Element | null)?.closest?.('.btn')
  if (!el || (el as HTMLButtonElement).disabled) return
  const id = ++seq
  const word = t(`skinComic.${WORDS[id % WORDS.length]}`)
  bursts.value = [...bursts.value.slice(-3), { id, x: e.clientX, y: e.clientY, word, fill: FILLS[id % FILLS.length]!, rot: (id * 37 % 30) - 15 }]
  const tm = setTimeout(() => { bursts.value = bursts.value.filter(b => b.id !== id); timers.delete(tm) }, 650)
  timers.add(tm)
}
// a starburst outline: 14 spikes, alternating radii
const SPIKES = Array.from({ length: 28 }, (_, i) => {
  const a = (i / 28) * Math.PI * 2
  const r = i % 2 ? 31 : (i % 4 ? 48 : 44)
  return `${(50 + Math.cos(a) * r).toFixed(1)},${(50 + Math.sin(a) * r * .8).toFixed(1)}`
}).join(' ')

const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') pop.value = false }
onMounted(() => {
  reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  document.addEventListener('pointerdown', onDown, true)
  window.addEventListener('keydown', onKey)
  nextTick(centre)
})
onUnmounted(() => {
  document.removeEventListener('pointerdown', onDown, true)
  window.removeEventListener('keydown', onKey)
  for (const tm of timers) clearTimeout(tm)
  timers.clear()
})
</script>

<template>
  <div class="comic-nav" :class="{ full }">
    <header class="mast">
      <NuxtLink to="/" class="logo" :aria-label="'bastion'">
        <svg class="star" viewBox="0 0 100 100" aria-hidden="true"><polygon :points="SPIKES" fill="#ffd83d" stroke="#111111" stroke-width="3" stroke-linejoin="round" /></svg>
        <span class="t1">{{ 'Bastion' }}</span><span class="t2">{{ 'Comics' }}</span>
      </NuxtLink>
      <span class="issue"><small>{{ 'No.' }}</small>{{ doy }}</span>
      <span class="tools">
        <JobsButton />
        <span class="live" :class="state"><i class="dot" /><span class="lt">{{ up }} · {{ stateText }}</span></span>
        <button type="button" class="cbtn" :aria-label="$t('skinComic.search')" @click="emit('search')"><Icon name="search" :size="18" /></button>
      </span>
    </header>

    <nav class="issues">
      <NuxtLink v-for="n in nav" :key="n.to" :to="n.to" class="tab" :class="{ on: n.to === path }">
        <Icon :name="n.icon" :size="15" /><span>{{ n.label }}</span>
        <span v-if="badge(n.to)" class="bdg">{{ badge(n.to) }}</span>
        <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
      </NuxtLink>
    </nav>

    <nav ref="bar" class="bubbles">
      <NuxtLink v-for="n in [...pins.pinned.value, ...(offTab ? [offTab] : [])]" :key="n.to" :to="n.to" class="bub" :class="{ on: n.to === path && !pop }">
        <Icon :name="n.icon" :size="18" /><span class="bl">{{ n.label }}</span>
        <span v-if="badge(n.to)" class="bdg">{{ badge(n.to) }}</span>
        <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
      </NuxtLink>
      <button type="button" class="bub more" :class="{ on: pop }" :aria-expanded="pop" @click="pop = !pop">
        <Icon name="grid" :size="18" /><span class="bl">{{ $t('skinComic.more') }}</span>
        <span v-if="moreBadge" class="bdg">{{ moreBadge }}</span>
      </button>
      <!-- full-screen pages (/chat) drop the masthead: its search and jobs ride on the bubble bar instead -->
      <template v-if="full">
        <span class="bjobs"><JobsButton /></span>
        <button type="button" class="bub srch" :aria-label="$t('skinComic.search')" @click="emit('search')"><Icon name="search" :size="18" /></button>
      </template>
    </nav>

    <button v-if="full" type="button" class="fab" :aria-label="$t('skinComic.pages')" :aria-expanded="pop" @click="pop = !pop">
      <svg viewBox="0 0 100 100" aria-hidden="true"><polygon :points="SPIKES" fill="#ffd83d" stroke="#111111" stroke-width="4" stroke-linejoin="round" /></svg>
      <Icon name="grid" :size="18" class="fi" />
    </button>
    <Transition name="cpop">
      <div v-if="pop" class="popover" role="menu">
        <div class="phead">
          <span class="pc">{{ editing ? $t('skinComic.pinCount', { n: pins.keys.value.length, max: pins.max }) : $t('skinComic.pages') }}</span>
          <button type="button" class="pedit" :class="{ on: editing }" :aria-pressed="editing" @click="editing = !editing">{{ editing ? $t('skinComic.done') : $t('skinComic.editTabs') }}</button>
        </div>
        <button v-for="n in nav" :key="n.to" type="button" class="pi"
          :class="{ on: !editing && n.to === path, pinned: editing && pins.isPinned(n.to), dim: editing && pins.full.value && !pins.isPinned(n.to) }"
          role="menuitem" @click="pick(n.to)">
          <Icon :name="n.icon" :size="16" /><span>{{ n.label }}</span>
          <span v-if="editing && pins.isPinned(n.to)" class="ppin"><Icon name="pin" :size="13" /></span>
          <span v-else-if="badge(n.to)" class="bdg">{{ badge(n.to) }}</span>
        </button>
        <button v-if="!editing" type="button" class="pi" @click="pop = false; emit('search')"><Icon name="search" :size="16" /><span>{{ $t('skinComic.search') }}</span></button>
      </div>
    </Transition>

    <div class="fx" aria-hidden="true">
      <div v-for="b in bursts" :key="b.id" class="burst" :style="{ left: `${b.x}px`, top: `${b.y}px`, '--r': `${b.rot}deg` }">
        <svg viewBox="0 0 100 100"><polygon :points="SPIKES" :fill="b.fill" stroke="#111111" stroke-width="3" stroke-linejoin="round" /></svg>
        <b>{{ b.word }}</b>
      </div>
    </div>
  </div>
</template>

<style scoped>
.comic-nav { --ink: var(--line-2); }
/* ---------- masthead ---------- */
.mast {
  position: relative; display: flex; align-items: center; gap: 14px; max-width: 1320px; margin: 0 auto; padding: 14px 28px 8px;
}
.logo { position: relative; display: flex; align-items: baseline; gap: 8px; padding: 6px 16px 6px 54px; color: var(--panel); text-decoration: none; transform: rotate(-2deg); }
.logo:hover { text-decoration: none; }
.star { position: absolute; left: -4px; top: 50%; width: 64px; height: 64px; margin-top: -32px; animation: cspin 30s linear infinite; }
.t1, .t2 { font-weight: 900; font-style: italic; text-transform: uppercase; line-height: 1; letter-spacing: .01em; -webkit-text-stroke: 1.5px var(--ink); paint-order: stroke fill; }
.t1 { position: relative; font-size: 34px; color: var(--comic-red); text-shadow: 3px 3px 0 var(--ink); }
.t2 { position: relative; font-size: 22px; color: var(--comic-yellow); text-shadow: 2px 2px 0 var(--ink); }
.issue { display: inline-flex; flex-direction: column; align-items: center; justify-content: center; min-width: 54px; padding: 4px 8px; font-weight: 900; font-size: 22px; line-height: 1; color: var(--ink); background: var(--panel); border: 3px solid var(--ink); box-shadow: 3px 3px 0 var(--ink); transform: rotate(3deg); }
.issue small { font-size: 9px; letter-spacing: .1em; }
.tools { margin-left: auto; display: flex; align-items: center; gap: 10px; }
.live { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; font-size: 12px; font-weight: 700; color: var(--ink); background: var(--panel); border: 2px solid var(--ink); border-radius: 999px; white-space: nowrap; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: var(--ok); border: 2px solid var(--ink); }
.live.warn .dot { background: var(--warn); } .live.bad .dot { background: var(--bad); }
.cbtn { display: grid; place-items: center; width: 40px; height: 40px; padding: 0; color: var(--ink); background: var(--comic-yellow); border: 2.5px solid var(--ink); border-radius: 50%; box-shadow: 3px 3px 0 var(--ink); cursor: pointer; }
.cbtn:active { transform: translate(2px, 2px); box-shadow: 1px 1px 0 var(--ink); }
.comic-nav :deep(.jt) { border: 2px solid var(--ink); background: var(--panel); color: var(--ink); font-weight: 700; box-shadow: 2px 2px 0 var(--ink); }

/* ---------- desktop issue tabs ---------- */
.issues { display: flex; flex-wrap: wrap; gap: 6px 4px; max-width: 1320px; margin: 0 auto; padding: 6px 28px 0; border-bottom: 3px solid var(--ink); }
.tab {
  position: relative; display: inline-flex; align-items: center; gap: 6px; min-height: 34px; padding: 6px 12px; margin-bottom: -3px;
  font-weight: 800; font-size: 13px; text-transform: uppercase; color: var(--ink); text-decoration: none;
  background: var(--panel); border: 3px solid var(--ink); border-radius: 8px 8px 0 0; transition: transform .12s;
}
.tab:hover { text-decoration: none; transform: translateY(-3px); }
.tab.on { background: var(--comic-yellow); border-bottom-color: var(--comic-yellow); transform: translateY(-4px); padding-bottom: 10px; margin-bottom: -7px; }
.bdg { min-width: 18px; padding: 0 5px; font-size: 11px; font-weight: 900; line-height: 16px; text-align: center; color: var(--panel); background: var(--bad); border: 2px solid var(--ink); border-radius: 999px; }
.cm { width: 10px; height: 10px; border-radius: 50%; background: var(--accent); border: 2px solid var(--ink); }
.cm.busy { animation: cblink 1.2s steps(2) infinite; }
.cm.input { background: var(--warn); }
@keyframes cblink { 50% { opacity: .3; } }
@keyframes cspin { to { transform: rotate(360deg); } }

/* ---------- phone speech bubbles ---------- */
.bubbles { display: none; }
.bubbles {
  position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; gap: 10px; align-items: flex-start; overflow-x: auto; scrollbar-width: none;
  height: calc(70px + env(safe-area-inset-bottom)); padding: 8px 12px env(safe-area-inset-bottom);
  background: var(--comic-yellow); border-top: 3px solid var(--ink);
  background-image: radial-gradient(circle, rgba(0, 0, 0, .14) 1.1px, transparent 1.5px); background-size: 8px 8px;
}
.bubbles::-webkit-scrollbar { display: none; }
.bub {
  position: relative; flex: none; display: inline-flex; align-items: center; gap: 6px; height: 42px; padding: 0 14px;
  font-weight: 800; font-size: 13px; text-transform: uppercase; color: var(--ink); text-decoration: none; white-space: nowrap;
  background: var(--panel); border: 2.5px solid var(--ink); border-radius: 22px; box-shadow: 2px 2px 0 var(--ink);
  -webkit-tap-highlight-color: transparent;
}
.bub:hover { text-decoration: none; }
.bub::after {
  content: ''; position: absolute; left: 18px; bottom: -8px; width: 12px; height: 12px; background: inherit;
  border-right: 2.5px solid var(--ink); border-bottom: 2.5px solid var(--ink); transform: skewX(-25deg) rotate(45deg); border-radius: 0 0 3px 0;
}
.bub:active { transform: translate(2px, 2px); box-shadow: none; }
.bub.on { background: var(--comic-red); color: var(--panel); }
.bub.on .bl { -webkit-text-stroke: .5px var(--ink); }
.bub .bdg, .bub .cm { position: absolute; top: -7px; right: -6px; }
.bub.srch { width: 46px; padding: 0; justify-content: center; cursor: pointer; font: inherit; }
.bub.srch::after { display: none; }
.bjobs { flex: none; display: flex; align-items: center; height: 42px; }
.bjobs:empty { display: none; }

/* ---------- full pages on desktop: a floating burst with every page ---------- */
.fab { position: fixed; z-index: 62; left: 14px; bottom: 14px; display: grid; place-items: center; width: 58px; height: 58px; padding: 0; border: 0; background: none; cursor: pointer; filter: drop-shadow(3px 3px 0 var(--ink)); }
.fab svg { position: absolute; inset: 0; width: 100%; height: 100%; }
.fab .fi { position: relative; color: var(--ink); }
.popover {
  position: fixed; z-index: 62; left: 14px; bottom: 82px; display: flex; flex-direction: column; gap: 4px; width: 220px; max-height: calc(100dvh - 120px); overflow-y: auto;
  padding: 10px; background: var(--panel); border: 3px solid var(--ink); border-radius: 14px; box-shadow: 5px 5px 0 var(--ink);
}
.pi { display: flex; align-items: center; gap: 8px; min-height: 34px; padding: 4px 10px; font: inherit; font-weight: 800; font-size: 13px; text-transform: uppercase; color: var(--ink); text-decoration: none; background: none; border: 2px solid transparent; border-radius: 8px; cursor: pointer; }
.pi:hover, .pi.on { text-decoration: none; background: var(--comic-yellow); border-color: var(--ink); }
.pi .bdg, .pi .ppin { margin-left: auto; }
.phead { display: flex; align-items: center; gap: 8px; padding: 0 2px 6px; margin-bottom: 2px; border-bottom: 2px dashed var(--ink); }
.pc { flex: 1; font-weight: 900; font-size: 12px; text-transform: uppercase; color: var(--ink); }
.pedit { min-height: 32px; padding: 0 12px; font: inherit; font-weight: 900; font-size: 12px; text-transform: uppercase; color: var(--ink); background: var(--comic-yellow); border: 2.5px solid var(--ink); border-radius: 999px; box-shadow: 2px 2px 0 var(--ink); cursor: pointer; }
.pedit.on { background: var(--comic-red); color: var(--panel); }
.pi.pinned { background: var(--comic-yellow); border-color: var(--ink); }
.pi.dim { opacity: .45; }
.ppin { display: grid; place-items: center; width: 22px; height: 22px; color: var(--panel); background: var(--comic-red); border: 2px solid var(--ink); border-radius: 50%; }
.cpop-enter-active { transition: transform .25s cubic-bezier(.34, 1.7, .64, 1), opacity .15s; transform-origin: 0 100%; }
.cpop-leave-active { transition: opacity .12s; }
.cpop-enter-from { transform: scale(.6) rotate(-6deg); opacity: 0; }
.cpop-leave-to { opacity: 0; }

/* ---------- onomatopoeia ---------- */
.fx { position: fixed; inset: 0; z-index: 95; pointer-events: none; overflow: hidden; }
.burst { position: absolute; width: 112px; height: 92px; margin: -46px 0 0 -56px; display: grid; place-items: center; animation: cburst .62s cubic-bezier(.2, 1.4, .4, 1) forwards; }
.burst svg { position: absolute; inset: 0; width: 100%; height: 100%; filter: drop-shadow(3px 3px 0 rgba(0, 0, 0, .9)); }
.burst b { position: relative; font-size: 22px; font-weight: 900; font-style: italic; letter-spacing: .02em; color: var(--comic-red); -webkit-text-stroke: 1.5px var(--ink); paint-order: stroke fill; transform: rotate(var(--r)); }
@keyframes cburst {
  0% { transform: scale(.2) rotate(calc(var(--r) * -2)); opacity: 1; }
  35% { transform: scale(1.18) rotate(var(--r)); opacity: 1; }
  55% { transform: scale(1) rotate(var(--r)); opacity: 1; }
  100% { transform: scale(1.08) translateY(-14px) rotate(var(--r)); opacity: 0; }
}

@media (max-width: 640px) {
  .mast { padding: calc(env(safe-area-inset-top, 0px) + 10px) 12px 4px; gap: 10px; }
  .logo { padding: 4px 8px 4px 40px; gap: 5px; }
  .star { width: 46px; height: 46px; margin-top: -23px; }
  .t1 { font-size: 24px; }
  .t2 { font-size: 15px; }
  .issue { min-width: 40px; font-size: 16px; padding: 3px 6px; }
  .live .lt { display: none; }
  .live { padding: 4px; }
  .issues { display: none; }
  .bubbles { display: flex; }
  .fab { display: none; }
  .popover { left: 12px; right: 12px; width: auto; bottom: calc(82px + env(safe-area-inset-bottom)); max-height: calc(100dvh - 180px); }
  .bub.more { cursor: pointer; font: inherit; font-weight: 800; font-size: 13px; }
  html.kb .bubbles { display: none; }
}
@media (max-width: 380px) { .t2 { display: none; } }
.full .mast, .full .issues { display: none; }
@media (prefers-reduced-motion: reduce) {
  .star, .cm.busy { animation: none; }
  .tab, .cpop-enter-active { transition: none; }
}
</style>

<style>
/* comic palette extras + room for the bubble bar; only while this skin is on */
html.skin-comic { --comic-yellow: rgba(255, 216, 61, 1); --comic-red: rgba(227, 38, 47, 1); --comic-blue: rgba(30, 91, 216, 1); }
/* see-through body so the newsprint Backdrop (z-index -1) shows; the tilted panel frames may poke a few px past the
   page edge on long panels: clip that sideways instead of letting the phone page wobble left and right */
html.skin-comic body { background: transparent; }
html.skin-comic main.wrap { overflow-x: clip; }
/* inked icons: a heavy outline with a light flat fill, like a coloured panel */
html.skin-comic svg.icon { stroke-width: 2.5; fill: color-mix(in srgb, currentColor 16%, transparent); }
@media (max-width: 640px) {
  html.skin-comic .shell.skinned { --tabbar: calc(74px + env(safe-area-inset-bottom)); }
  html.skin-comic main.wrap { padding-bottom: calc(var(--tabbar) + 24px); }
}
</style>
