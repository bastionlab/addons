<script setup lang="ts">
/**
 * The Bastion Times masthead. Desktop: weather ear (live state as Fair/Clouds/Storm) · the paper's name in a heavy
 * display serif · circulation ear (the `up` count, jobs, search); a dateline between double rules (weekday + date,
 * Vol. <year>, No. <day of year>, Price: free); then the section index (small caps, sticky). When the agent is
 * down a red BREAKING ticker runs under the masthead with the state text.
 * Phone: a compact masthead on top and a bottom bar of the viewer's pinned sections (useNavPins) + "Sections", which
 * opens the newspaper's index as a full sheet (where "edit tabs" picks the pinned ones).
 */
const props = withDefaults(defineProps<{
  nav?: { to: string, icon: string, label: string }[], path?: string
  badge?: (to: string) => number, mark?: (to: string) => string
  state?: string, stateText?: string, up?: string, full?: boolean
}>(), { nav: () => [], path: '/', badge: () => 0, mark: () => '', state: 'ok', stateText: '', up: '', full: false })
const emit = defineEmits<{ search: [] }>()
const { t } = useI18n()

const nav = computed(() => props.nav ?? [])
const here = computed(() => nav.value.find(n => n.to === props.path))
const sheet = ref(false)
watch(() => props.path, () => (sheet.value = false))
const pins = useNavPins(() => nav.value)
const { editing } = pins
const offTab = computed(() => (here.value && !pins.isPinned(here.value.to) ? here.value : null))
const moreBadge = computed(() => nav.value.some(n => !pins.isPinned(n.to) && props.badge(n.to) > 0))
watch(sheet, v => { if (!v) editing.value = false })
function go(to: string) { if (editing.value) { pins.toggle(to); return } sheet.value = false; navigateTo(to) }
function search() { sheet.value = false; emit('search') }

const now = ref(new Date())
const year = computed(() => now.value.getFullYear())
const doy = computed(() => { const d = now.value; return Math.floor((d.getTime() - new Date(d.getFullYear(), 0, 0).getTime()) / 864e5) })
const longDate = computed(() => fmtDate(now.value, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }))
const shortDate = computed(() => fmtDate(now.value, { weekday: 'short', day: 'numeric', month: 'short' }))
const weather = computed(() => (props.state === 'bad' ? 'storm' : props.state === 'warn' ? 'clouds' : 'fair'))
const pageRef = (i: number) => `${String.fromCharCode(65 + Math.floor(i / 3))}${(i % 3) + 1}`
const breaking = computed(() => props.state === 'bad')
const news = computed(() => props.stateText || t('skinBroadsheet.storm'))

let tick: ReturnType<typeof setInterval> | undefined
const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') sheet.value = false }
onMounted(() => {
  tick = setInterval(() => (now.value = new Date()), 60_000)
  window.addEventListener('keydown', onKey)
})
onUnmounted(() => { if (tick) clearInterval(tick); window.removeEventListener('keydown', onKey) })
</script>

<template>
  <div class="bs-nav" :class="{ full }">
    <!-- ======== desktop masthead ======== -->
    <header class="mast">
      <div class="ear wx" :class="state">
        <span class="el">{{ $t('skinBroadsheet.weather') }}</span>
        <svg v-if="weather === 'fair'" class="wi" viewBox="0 0 40 40" aria-hidden="true">
          <circle cx="20" cy="20" r="7" fill="none" stroke="currentColor" stroke-width="2" />
          <g stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M20 4v5M20 31v5M4 20h5M31 20h5M8.7 8.7l3.5 3.5M27.8 27.8l3.5 3.5M8.7 31.3l3.5-3.5M27.8 12.2l3.5-3.5" /></g>
        </svg>
        <svg v-else-if="weather === 'clouds'" class="wi" viewBox="0 0 40 40" aria-hidden="true">
          <circle cx="14" cy="14" r="5" fill="none" stroke="currentColor" stroke-width="1.6" />
          <path d="M10 30h20a6 6 0 0 0 0-12 8 8 0 0 0-15-1 6.5 6.5 0 0 0-5 13z" fill="currentColor" fill-opacity=".12" stroke="currentColor" stroke-width="2" />
        </svg>
        <svg v-else class="wi" viewBox="0 0 40 40" aria-hidden="true">
          <path d="M9 24h21a6 6 0 0 0 0-12 8 8 0 0 0-15-1 6.5 6.5 0 0 0-6 13z" fill="currentColor" fill-opacity=".2" stroke="currentColor" stroke-width="2" />
          <path d="M21 25l-4 7h5l-3 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" />
        </svg>
        <b class="ew">{{ $t(`skinBroadsheet.${weather}`) }}</b>
      </div>
      <NuxtLink to="/" class="name">
        <span class="nm">{{ $t('skinBroadsheet.masthead') }}</span>
        <span class="motto">{{ `“${$t('skinBroadsheet.motto')}”` }}</span>
      </NuxtLink>
      <div class="ear circ">
        <span class="el">{{ $t('skinBroadsheet.circulation') }}</span>
        <b class="ew">{{ up || '–' }}</b>
        <span class="tools">
          <JobsButton />
          <button type="button" class="ib" :aria-label="$t('skinBroadsheet.search')" @click="emit('search')"><Icon name="search" :size="20" /></button>
        </span>
      </div>
    </header>
    <div class="dateline">
      <span>{{ $t('skinBroadsheet.vol', { n: year }) }}</span>
      <span class="dl-date">{{ longDate }}</span>
      <span>{{ $t('skinBroadsheet.no', { n: doy }) }}</span>
      <span class="dl-price">{{ $t('skinBroadsheet.price') }}</span>
    </div>

    <!-- ======== phone compact masthead ======== -->
    <header class="pmast">
      <NuxtLink to="/" class="pname">{{ $t('skinBroadsheet.masthead') }}</NuxtLink>
      <div class="pline">
        <span class="pwx" :class="state">{{ $t(`skinBroadsheet.${weather}`) }}</span>
        <span>{{ shortDate }}</span>
        <span>{{ $t('skinBroadsheet.no', { n: doy }) }}</span>
        <span class="pup">{{ up }}</span>
      </div>
    </header>

    <!-- ======== breaking news ======== -->
    <div v-if="breaking" class="ticker" role="status">
      <b class="tk-l">{{ $t('skinBroadsheet.breaking') }}</b>
      <div class="tk-w">
        <div class="tk-t">
          <span v-for="i in 6" :key="i">{{ news }}<i class="star">{{ '✶' }}</i></span>
        </div>
      </div>
    </div>

    <!-- ======== desktop section index (sticky) ======== -->
    <nav class="index">
      <NuxtLink v-for="n in nav" :key="n.to" :to="n.to" class="ix" :class="{ on: n.to === path }">
        {{ n.label }}<sup v-if="badge(n.to)" class="bd">{{ badge(n.to) }}</sup><sup v-else-if="mark(n.to)" class="mk" :class="mark(n.to)">{{ '•' }}</sup>
      </NuxtLink>
    </nav>

    <!-- ======== phone bottom bar / desktop full-page key ======== -->
    <div class="pbar">
      <NuxtLink v-for="n in [...pins.pinned.value, ...(offTab ? [offTab] : [])]" :key="n.to" :to="n.to" class="pt" :class="{ on: n.to === path && !sheet }">
        <Icon :name="n.icon" :size="18" /><span class="ptl">{{ n.label }}</span>
        <span v-if="badge(n.to)" class="dotb" /><span v-else-if="mark(n.to)" class="mk pmk" :class="mark(n.to)">{{ '•' }}</span>
      </NuxtLink>
      <span class="tools"><JobsButton /></span>
      <button type="button" class="sbtn" :aria-expanded="sheet" @click="sheet = !sheet">
        <Icon name="grid" :size="18" /><span>{{ $t('skinBroadsheet.sections') }}</span>
        <span v-if="moreBadge" class="dotb" />
      </button>
    </div>
    <button type="button" class="fkey" @click="sheet = true"><Icon name="grid" :size="18" /><span>{{ $t('skinBroadsheet.sections') }}</span></button>

    <Transition name="bsheet">
      <div v-if="sheet" class="scrim" @click.self="sheet = false">
        <div class="sheet" role="dialog" :aria-label="$t('skinBroadsheet.index')">
          <div class="sh-top">
            <span class="sh-name">{{ $t('skinBroadsheet.masthead') }}</span>
            <button type="button" class="ib" :aria-label="$t('skinBroadsheet.search')" @click="search"><Icon name="search" :size="20" /></button>
            <button type="button" class="xb" :class="{ on: editing }" :aria-pressed="editing" @click="editing = !editing">{{ editing ? $t('skinBroadsheet.done') : $t('skinBroadsheet.editTabs') }}</button>
            <button type="button" class="xb" @click="sheet = false">{{ $t('skinBroadsheet.close') }}</button>
          </div>
          <h2 class="sh-h">{{ $t('skinBroadsheet.index') }}</h2>
          <p class="sh-sub">{{ editing ? $t('skinBroadsheet.pinHint', { n: pins.keys.value.length, max: pins.max }) : `${$t('skinBroadsheet.inside')} · ${longDate}` }}</p>
          <ul class="toc">
            <li v-for="(n, i) in nav" :key="n.to">
              <button type="button" class="row" :class="{ on: !editing && n.to === path, pinned: editing && pins.isPinned(n.to), dim: editing && pins.full.value && !pins.isPinned(n.to) }" :aria-pressed="editing ? pins.isPinned(n.to) : undefined" @click="go(n.to)">
                <Icon :name="n.icon" :size="20" />
                <span class="rl">{{ n.label }}</span>
                <span v-if="badge(n.to)" class="bd">{{ badge(n.to) }}</span>
                <span v-else-if="mark(n.to)" class="mk" :class="mark(n.to)">{{ '•' }}</span>
                <span class="lead" />
                <span v-if="editing" class="pg">{{ pins.isPinned(n.to) ? '✓' : '' }}</span>
                <span v-else class="pg">{{ pageRef(i) }}</span>
              </button>
            </li>
          </ul>
          <div class="sh-foot">
            <span :class="['pwx', state]">{{ $t('skinBroadsheet.weather') }}: {{ $t(`skinBroadsheet.${weather}`) }}</span>
            <span>{{ $t('skinBroadsheet.circulation') }}: {{ up }}</span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.bs-nav { display: contents; --ink: var(--text); --disp: "Playfair Display", "Bodoni 72", Didot, "Bodoni MT", "Abril Fatface", "Noto Serif Display", Georgia, "Times New Roman", serif; }

/* ---------- desktop masthead ---------- */
.mast {
  display: grid; grid-template-columns: 170px minmax(0, 1fr) 170px; align-items: center; gap: 18px;
  max-width: 1280px; margin: 0 auto; padding: 18px 28px 8px;
}
.ear {
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; min-height: 92px; padding: 6px 8px;
  border: 1px solid var(--ink); outline: 1px solid var(--ink); outline-offset: 2px; text-align: center; color: var(--ink);
}
.el { font-size: 10.5px; font-variant: small-caps; letter-spacing: .14em; text-transform: lowercase; color: var(--muted); }
.ew { font-family: var(--disp); font-size: 20px; font-weight: 800; font-style: italic; }
.wi { width: 30px; height: 30px; color: var(--ink); }
.wx.warn .wi, .wx.warn .ew { color: var(--warn); }
.wx.bad .wi, .wx.bad .ew { color: var(--bad); }
.tools { display: inline-flex; align-items: center; gap: 4px; }
.tools:empty { display: none; }
.bs-nav :deep(.jt) { border-radius: 0; background: transparent; border-color: var(--ink); color: var(--ink); }
.ib { display: grid; place-items: center; width: 36px; height: 36px; padding: 0; background: none; border: 1px solid transparent; color: var(--ink); cursor: pointer; }
.ib:hover { border-color: var(--ink); }
.name { display: flex; flex-direction: column; align-items: center; min-width: 0; color: var(--ink) !important; text-decoration: none; }
.name:hover { text-decoration: none; }
.nm {
  font-family: var(--disp); font-weight: 900; font-size: clamp(38px, 5.6vw, 76px); line-height: 1; letter-spacing: -.01em;
  white-space: nowrap; text-shadow: .5px .5px 0 rgba(28, 24, 19, .35);
}
.motto { margin-top: 6px; font-style: italic; font-size: 13px; color: var(--muted); }
.dateline {
  display: flex; justify-content: space-between; align-items: center; gap: 12px; max-width: 1224px; margin: 0 auto 0; padding: 5px 4px;
  border-top: 3px double var(--ink); border-bottom: 3px double var(--ink);
  font-size: 12.5px; font-variant: small-caps; letter-spacing: .08em; color: var(--ink);
}
.dl-date { font-weight: 700; }

/* ---------- section index (sticky on desktop) ---------- */
.index {
  position: sticky; top: 0; z-index: 40; display: flex; flex-wrap: nowrap; justify-content: safe center; gap: 0; overflow-x: auto; scrollbar-width: none;
  max-width: 1224px; margin: 0 auto; padding: 0 4px; background: var(--bg); border-bottom: 1px solid var(--ink);
  box-shadow: 0 6px 12px -8px rgba(60, 45, 20, .35);
}
.ix {
  position: relative; flex: none; display: inline-flex; align-items: center; min-height: 38px; white-space: nowrap; padding: 0 12px; color: var(--ink) !important; text-decoration: none;
  font-variant: small-caps; text-transform: lowercase; letter-spacing: .1em; font-size: 15px;
}
.ix + .ix::before { content: ''; position: absolute; left: 0; top: 11px; bottom: 11px; border-left: 1px solid var(--line-2); }
.ix:hover { text-decoration: underline; text-underline-offset: 4px; }
.ix.on { font-weight: 800; text-decoration: underline; text-decoration-thickness: 2px; text-underline-offset: 5px; }
sup { font-size: 10px; margin-left: 2px; }
.bd { color: var(--bad); font-weight: 800; font-variant: normal; }
.mk { color: var(--accent); font-size: 16px; line-height: 0; }
.mk.input { color: var(--warn); }
.mk.busy { animation: bsblink 1.2s ease-in-out infinite; }
@keyframes bsblink { 50% { opacity: .25; } }

/* ---------- breaking news ticker ---------- */
.ticker { display: flex; align-items: stretch; max-width: 1224px; margin: 6px auto 0; height: 32px; background: var(--bad); color: var(--bg); overflow: hidden; }
.tk-l {
  flex: none; display: flex; align-items: center; padding: 0 12px; background: var(--ink); color: var(--bg);
  font-family: var(--disp); font-style: italic; font-weight: 900; text-transform: uppercase; letter-spacing: .06em; font-size: 14px;
}
.tk-w { flex: 1; min-width: 0; overflow: hidden; display: flex; align-items: center; }
.tk-t { display: flex; flex: none; white-space: nowrap; animation: bstick 22s linear infinite; font-weight: 700; font-size: 14px; }
.tk-t span { padding-left: 18px; }
.star { font-style: normal; padding-left: 18px; opacity: .8; }
@keyframes bstick { from { transform: translateX(0); } to { transform: translateX(-50%); } }

/* ---------- phone pieces ---------- */
.pmast, .pbar, .fkey { display: none; }
.pbar {
  position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; height: calc(56px + env(safe-area-inset-bottom)); padding: 0 8px env(safe-area-inset-bottom);
  align-items: center; gap: 6px; background: var(--bg); border-top: 3px double var(--ink); box-shadow: 0 -6px 16px rgba(60, 45, 20, .18);
}
.sbtn {
  position: relative; display: inline-flex; align-items: center; gap: 8px; height: 40px; padding: 0 14px; background: var(--ink); color: var(--bg);
  border: 0; font: inherit; font-variant: small-caps; text-transform: lowercase; letter-spacing: .1em; font-size: 16px; font-weight: 700; cursor: pointer;
}
.dotb { position: absolute; top: 5px; right: 5px; width: 8px; height: 8px; border-radius: 50%; background: var(--bad); box-shadow: 0 0 0 2px var(--ink); }
.pt {
  position: relative; flex: 1 1 0; min-width: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px; height: 48px;
  color: var(--muted); text-decoration: none; -webkit-tap-highlight-color: transparent;
}
.pt:hover { text-decoration: none; }
.ptl { max-width: 100%; font-size: 12px; font-variant: small-caps; text-transform: lowercase; letter-spacing: .05em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pt.on { color: var(--ink); }
.pt.on .ptl { font-weight: 800; text-decoration: underline; text-underline-offset: 3px; }
.pt .dotb { top: 4px; right: calc(50% - 16px); }
.pmk { position: absolute; top: 8px; right: calc(50% - 14px); }
.xb.on { background: var(--ink); color: var(--bg); }
.row.pinned .rl { font-weight: 800; }
.row.pinned .icon { color: var(--ink); }
.row.dim { opacity: .45; }
.fkey {
  position: fixed; z-index: 61; left: 12px; bottom: 12px; align-items: center; gap: 6px; height: 36px; padding: 0 12px;
  background: var(--ink); color: var(--bg); border: 0; font: inherit; font-variant: small-caps; text-transform: lowercase; letter-spacing: .1em; cursor: pointer;
  box-shadow: 3px 3px 0 rgba(28, 24, 19, .25);
}
.pmast { padding: calc(env(safe-area-inset-top, 0px) + 6px) 12px 0; text-align: center; }
.pname { display: block; color: var(--ink) !important; text-decoration: none; font-family: var(--disp); font-weight: 900; font-size: 30px; line-height: 1.05; white-space: nowrap; }
.pline {
  display: flex; justify-content: space-between; gap: 6px; margin-top: 5px; padding: 3px 0; border-top: 3px double var(--ink); border-bottom: 3px double var(--ink);
  font-size: 11.5px; font-variant: small-caps; letter-spacing: .05em; color: var(--ink); white-space: nowrap;
}
.pwx { font-weight: 800; font-style: italic; }
.pwx.warn { color: var(--warn); }
.pwx.bad { color: var(--bad); }
.pup { overflow: hidden; text-overflow: ellipsis; min-width: 0; }

/* ---------- the index sheet ---------- */
.scrim { position: fixed; inset: 0; z-index: 80; background: rgba(28, 24, 19, .45); }
.sheet {
  position: absolute; inset: auto 0 0 0; max-height: calc(100dvh - 24px); overflow-y: auto; max-width: 560px; margin: 0 auto;
  padding: 12px 18px calc(18px + env(safe-area-inset-bottom)); background: var(--bg); color: var(--ink);
  border-top: 6px double var(--ink); box-shadow: 0 -18px 40px rgba(28, 24, 19, .35); transform-origin: 50% 100%;
}
.sh-top { display: flex; align-items: center; gap: 6px; }
.xb { min-height: 36px; padding: 0 10px; background: none; border: 1px solid var(--ink); color: var(--ink); font: inherit; font-variant: small-caps; text-transform: lowercase; letter-spacing: .08em; cursor: pointer; }
.sh-name { flex: 1; font-family: var(--disp); font-weight: 900; font-size: 20px; }
.sh-h { margin: 8px 0 0; font-family: var(--disp); font-weight: 900; font-size: 40px; line-height: 1; text-transform: uppercase; letter-spacing: .04em; text-align: center; border-bottom: 1px solid var(--ink); padding-bottom: 6px; }
.sh-sub { margin: 6px 0 10px; text-align: center; font-style: italic; font-size: 13px; color: var(--muted); }
.toc { list-style: none; margin: 0; padding: 0; columns: 1; }
.row {
  display: flex; align-items: center; gap: 10px; width: 100%; min-height: 44px; padding: 0 2px; background: none; border: 0; border-bottom: 1px dotted var(--line-2);
  color: var(--ink); font: inherit; font-size: 17px; text-align: left; cursor: pointer;
}
.row .icon { flex: none; color: var(--muted); }
.rl { font-variant: small-caps; text-transform: lowercase; letter-spacing: .06em; }
.row.on .rl { font-weight: 800; text-decoration: underline; text-underline-offset: 4px; }
.row .bd { font-size: 12px; }
.lead { flex: 1; }
.pg { flex: none; font-family: var(--disp); font-weight: 800; font-style: italic; color: var(--accent); }
.sh-foot { display: flex; justify-content: space-between; gap: 10px; margin-top: 12px; padding-top: 6px; border-top: 3px double var(--ink); font-size: 12.5px; font-variant: small-caps; letter-spacing: .05em; }
.bsheet-enter-active, .bsheet-leave-active { transition: opacity .25s; }
.bsheet-enter-active .sheet { transition: transform .35s cubic-bezier(.2, .8, .3, 1); }
.bsheet-leave-active .sheet { transition: transform .2s ease-in; }
.bsheet-enter-from, .bsheet-leave-to { opacity: 0; }
.bsheet-enter-from .sheet, .bsheet-leave-to .sheet { transform: translateY(40%) rotateX(18deg); }

/* full-screen pages on desktop (/chat): no masthead, a Sections key in the corner */
@media (min-width: 641px) {
  .full .mast, .full .dateline, .full .index, .full .ticker { display: none; }
  .full .fkey { display: inline-flex; }
}
@media (min-width: 641px) and (max-width: 900px) {
  .mast { grid-template-columns: 120px minmax(0, 1fr) 120px; padding: 14px 16px 6px; gap: 10px; }
  .ear { min-height: 80px; }
  .dateline, .index, .ticker { margin-left: 16px; margin-right: 16px; }
  .dl-price { display: none; }
}
@media (min-width: 901px) and (max-width: 1280px) { .dateline, .index, .ticker { margin-left: 28px; margin-right: 28px; } }
@media (max-width: 640px) {
  .mast, .dateline, .index { display: none; }
  .pmast { display: block; }
  .pbar { display: flex; }
  .sbtn { padding: 0 10px; font-size: 14px; gap: 6px; }
  .full .pmast { display: none; }
  .ticker { margin: 6px 12px 0; height: 30px; }
  .tk-l { font-size: 12px; padding: 0 8px; }
  html.kb .pbar { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  .tk-t { animation: none; }
  .mk.busy { animation: none; }
  .bsheet-enter-active .sheet, .bsheet-leave-active .sheet { transition: none; }
}
</style>

<style>
/* only while this skin is on: serif type, paper grain for articles, sticky offsets, room for the phone bar */
html.skin-broadsheet {
  --bs-serif: "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", "Noto Serif", Georgia, "Times New Roman", "Bastion Emoji", serif;
  --bs-disp: "Playfair Display", "Bodoni 72", Didot, "Bodoni MT", "Abril Fatface", "Noto Serif Display", Georgia, "Times New Roman", serif;
  --bs-grain: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .11 0 0 0 0 .09 0 0 0 0 .07 0 0 0 .09 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
  --ptabs-top: 38px;
}
html.skin-broadsheet body { font-family: var(--bs-serif); }
/* engraved look: thin ink strokes; emoji print in ink too (one-colour font, see SKINS.md) */
html.skin-broadsheet svg.icon { stroke-width: 1.4; stroke-linecap: butt; }
html.skin-broadsheet .shell.skinned { --tabbar: 0px; }
@media (max-width: 640px) {
  html.skin-broadsheet { --ptabs-top: 0px; }
  html.skin-broadsheet .shell.skinned { --tabbar: calc(56px + env(safe-area-inset-bottom)); }
  html.skin-broadsheet main.wrap { padding-bottom: calc(var(--tabbar) + 24px); }
}
/* column rules between grid columns, like a broadsheet page (articles are opaque paper, so the rule shows in the gutters) */
@media (min-width: 761px) {
  html.skin-broadsheet main.wrap .grid.cols-2, html.skin-broadsheet main.wrap .grid.cols-3 {
    background: linear-gradient(90deg, transparent calc(50% - .5px), var(--line-2) calc(50% - .5px), var(--line-2) calc(50% + .5px), transparent calc(50% + .5px));
  }
}
@media (min-width: 1101px) {
  html.skin-broadsheet main.wrap .grid.cols-3 {
    background:
      linear-gradient(90deg, transparent calc((100% - 28px) / 3 + 6.5px), var(--line-2) calc((100% - 28px) / 3 + 6.5px), var(--line-2) calc((100% - 28px) / 3 + 7.5px), transparent calc((100% - 28px) / 3 + 7.5px)),
      linear-gradient(90deg, transparent calc((100% - 28px) * 2 / 3 + 20.5px), var(--line-2) calc((100% - 28px) * 2 / 3 + 20.5px), var(--line-2) calc((100% - 28px) * 2 / 3 + 21.5px), transparent calc((100% - 28px) * 2 / 3 + 21.5px));
  }
}
</style>
