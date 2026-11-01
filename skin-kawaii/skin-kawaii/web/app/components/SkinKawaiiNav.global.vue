<script setup lang="ts">
/**
 * Navigation, the cute way. Phone: a floating bubble bar (the pinned pages + the open one, jelly icons, the open page
 * wears a bow, label beside it; a "more" bubble opens every page and "edit tabs" for the pins) with the cat mascot sitting on its right end, plus a small top row (brand, live dot, jobs, search).
 * Desktop: a "sticker sheet" sidebar, every page a tilted sticker that straightens on hover / when open, the cat
 * sitting at the bottom. The cat blinks, hops on page changes and, when tapped, pops hearts and says something nice.
 */
const props = withDefaults(defineProps<{
  nav?: { to: string, icon: string, label: string }[], path?: string
  badge?: (to: string) => number, mark?: (to: string) => string
  state?: string, stateText?: string, up?: string, full?: boolean
}>(), { nav: () => [], path: '/', badge: () => 0, mark: () => '', state: 'ok', stateText: '', up: '', full: false })
const emit = defineEmits<{ search: [] }>()
const { t } = useI18n()

const TILT = [-2.5, 1.8, -1.2, 2.4, -1.8, 1.1, -2.1, 1.5]
const tilt = (i: number) => `${TILT[i % TILT.length]}deg`
const hue = (i: number) => `hsl(${(330 + i * 47) % 360} 85% 90%)`

// phone bar: the viewer's pinned pages (+ the open one when it isn't pinned), "more" opens every page
const { pinned, isPinned, toggle, editing, full: pinsFull, max, keys } = useNavPins(() => props.nav)
const bar = computed(() => {
  const here = props.nav.find(n => n.to === props.path)
  return here && !isPinned(here.to) ? [...pinned.value, here] : pinned.value
})
const idx = (to: string) => Math.max(0, props.nav.findIndex(n => n.to === to))
const more = ref(false)
const moreBadge = computed(() => props.nav.filter(n => !isPinned(n.to)).reduce((s, n) => s + (props.badge(n.to) || 0), 0))
function pick(to: string) { if (editing.value) return toggle(to); more.value = false; navigateTo(to) }
watch(more, v => { if (!v) editing.value = false })
watch(() => props.path, () => (more.value = false))

// the bar scrolls on a phone: keep the open page's bubble in view
const strip = ref<HTMLElement | null>(null)
function reveal() {
  nextTick(() => (strip.value?.querySelector('.bub.on') as HTMLElement | null)?.scrollIntoView({ block: 'nearest', inline: 'center' }))
}

// mascot
const paused = ref(false)
const hop = ref(false)
const said = ref('')
const hearts = ref<{ id: number, x: number, r: number, d: number }[]>([])
let hid = 0
let last = 0
const timers = new Set<ReturnType<typeof setTimeout>>()
const later = (fn: () => void, ms: number) => { const h = setTimeout(() => { timers.delete(h); fn() }, ms); timers.add(h) }
let sayTimer: ReturnType<typeof setTimeout> | undefined
function doHop() { hop.value = false; nextTick(() => { hop.value = true; later(() => (hop.value = false), 650) }) }
function pet() {
  doHop()
  for (let i = 0; i < 6; i++) {
    const id = ++hid
    hearts.value.push({ id, x: Math.round(Math.random() * 60 - 30), r: Math.round(Math.random() * 50 - 25), d: Math.round(Math.random() * 160) })
    later(() => (hearts.value = hearts.value.filter(h => h.id !== id)), 1300)
  }
  let n = last
  while (n === last) n = 1 + Math.floor(Math.random() * 10)
  last = n
  said.value = t(`skinKawaii.msg.m${n}`)
  clearTimeout(sayTimer)
  sayTimer = setTimeout(() => (said.value = ''), 3000)
}
watch(() => props.path, () => { doHop(); reveal() })

const onVis = () => (paused.value = document.hidden)
onMounted(() => { onVis(); document.addEventListener('visibilitychange', onVis); reveal() })
onUnmounted(() => {
  document.removeEventListener('visibilitychange', onVis)
  clearTimeout(sayTimer)
  for (const h of timers) clearTimeout(h)
})
</script>

<template>
  <div class="kw-nav" :class="{ full }">
    <!-- phone: small top row -->
    <div v-if="!full" class="top">
      <NuxtLink to="/" class="brand"><span class="heart">{{ '♡' }}</span>{{ 'bastion' }}<span class="dot" :class="state" :title="stateText" /></NuxtLink>
      <span class="upt">{{ up }}</span>
      <JobsButton />
      <button type="button" class="round" :aria-label="$t('skinKawaii.search')" @click="emit('search')"><Icon name="search" :size="18" /></button>
    </div>

    <!-- desktop: the sticker sheet -->
    <aside class="sheet">
      <NuxtLink to="/" class="brand big"><span class="heart">{{ '♡' }}</span><span class="bl">{{ 'bastion' }}</span><span class="dot" :class="state" :title="stateText" /></NuxtLink>
      <button type="button" class="find" :aria-label="$t('skinKawaii.search')" @click="emit('search')"><Icon name="search" :size="16" /><span class="bl">{{ $t('skinKawaii.search') }}</span></button>
      <div class="jobs"><JobsButton /></div>
      <nav class="stickers" :aria-label="$t('skinKawaii.pages')">
        <NuxtLink v-for="(n, i) in nav" :key="n.to" :to="n.to" class="sticker" :class="{ on: n.to === path }" :style="{ '--tilt': tilt(i) }" :title="n.label">
          <span class="si" :style="{ background: hue(i) }"><Icon :name="n.icon" :size="17" /></span>
          <span class="bl sl">{{ n.label }}</span>
          <span v-if="badge(n.to)" class="badge">{{ badge(n.to) }}</span>
          <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
          <svg v-if="n.to === path" class="bow" viewBox="0 0 24 14" width="22" height="13" aria-hidden="true"><path d="M12 7C8 1 2 1 2 7s6 6 10 0z" fill="#ff7db5" /><path d="M12 7c4-6 10-6 10 0s-6 6-10 0z" fill="#ff7db5" /><circle cx="12" cy="7" r="2.6" fill="#e2508f" /></svg>
        </NuxtLink>
      </nav>
      <div class="foot"><span class="bl">{{ up }}</span></div>
    </aside>

    <!-- phone: the bubble bar -->
    <nav class="bubbles">
      <div ref="strip" class="strip">
        <NuxtLink v-for="n in bar" :key="n.to" :to="n.to" class="bub" :class="{ on: n.to === path && !more }" :aria-label="n.label">
          <span class="bi" :style="{ background: n.to === path && !more ? hue(idx(n.to)) : undefined }"><Icon :name="n.icon" :size="20" /></span>
          <span v-if="n.to === path && !more" class="bl2">{{ n.label }}</span>
          <svg v-if="n.to === path && !more" class="bow" viewBox="0 0 24 14" width="20" height="12" aria-hidden="true"><path d="M12 7C8 1 2 1 2 7s6 6 10 0z" fill="#ff7db5" /><path d="M12 7c4-6 10-6 10 0s-6 6-10 0z" fill="#ff7db5" /><circle cx="12" cy="7" r="2.6" fill="#e2508f" /></svg>
          <span v-if="badge(n.to)" class="badge">{{ badge(n.to) }}</span>
          <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
        </NuxtLink>
        <button type="button" class="bub" :class="{ on: more }" :aria-expanded="more" :aria-label="$t('skinKawaii.more')" @click="more = !more">
          <span class="bi" :style="{ background: more ? hue(3) : undefined }"><Icon name="grid" :size="20" /></span>
          <span v-if="more" class="bl2">{{ $t('skinKawaii.more') }}</span>
          <span v-if="moreBadge" class="badge">{{ moreBadge }}</span>
        </button>
      </div>
      <span class="catslot" />
    </nav>
    <Transition name="kw-say">
      <div v-if="more" class="kscrim" @click.self="more = false">
        <div class="kmore" role="dialog" :aria-label="$t('skinKawaii.pages')">
          <div class="khead">
            <b>{{ editing ? $t('skinKawaii.pinHint', { n: keys.length, max }) : $t('skinKawaii.pages') }}</b>
            <button type="button" class="kedit" :class="{ on: editing }" :aria-pressed="editing" @click="editing = !editing">{{ editing ? $t('skinKawaii.done') : $t('skinKawaii.editTabs') }}</button>
          </div>
          <div class="kgrid">
            <button v-for="(n, i) in nav" :key="n.to" type="button" class="kpage" :class="{ on: n.to === path && !editing, pinned: editing && isPinned(n.to), dim: editing && pinsFull && !isPinned(n.to) }" @click="pick(n.to)">
              <span class="si" :style="{ background: hue(i) }"><Icon :name="n.icon" :size="20" /></span>
              <span class="kl">{{ n.label }}</span>
              <span v-if="editing && isPinned(n.to)" class="kpin">{{ '♥' }}</span>
              <span v-else-if="badge(n.to)" class="badge">{{ badge(n.to) }}</span>
              <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- the mascot -->
    <div class="mascot" :class="{ paused, hop }">
      <Transition name="kw-say"><div v-if="said" class="bubble" role="status">{{ said }}</div></Transition>
      <span v-for="h in hearts" :key="h.id" class="pop" :style="{ '--x': `${h.x}px`, '--r': `${h.r}deg`, animationDelay: `${h.d}ms` }">{{ '♥' }}</span>
      <button type="button" class="cat" :aria-label="$t('skinKawaii.mascot')" @click="pet">
        <svg viewBox="0 0 80 72" width="72" height="65" aria-hidden="true">
          <path class="tail" d="M62 60c10 0 15-6 13-14-1-5-6-6-7-2" fill="none" stroke="#7a5469" stroke-width="5" stroke-linecap="round" />
          <path class="tail" d="M62 60c10 0 15-6 13-14-1-5-6-6-7-2" fill="none" stroke="#ffe9d6" stroke-width="2.6" stroke-linecap="round" />
          <ellipse cx="40" cy="54" rx="27" ry="16" fill="#fff4e8" stroke="#7a5469" stroke-width="2" />
          <path d="M19 24 16 6l15 10zM61 24l3-18-15 10z" fill="#fff4e8" stroke="#7a5469" stroke-width="2" stroke-linejoin="round" />
          <path d="M20 19l-1.6-8 7 4.6zM60 19l1.6-8-7 4.6z" fill="#ffb8d4" />
          <ellipse cx="40" cy="33" rx="24" ry="18.5" fill="#fff4e8" stroke="#7a5469" stroke-width="2" />
          <path d="M33 16c2 3 5 3 7 0 2 3 5 3 7 0" fill="none" stroke="#f2c9a8" stroke-width="2" stroke-linecap="round" />
          <g class="eyes">
            <ellipse cx="31" cy="32" rx="2.8" ry="3.4" fill="#4a3043" />
            <ellipse cx="49" cy="32" rx="2.8" ry="3.4" fill="#4a3043" />
            <circle cx="32" cy="31" r=".9" fill="#ffffff" />
            <circle cx="50" cy="31" r=".9" fill="#ffffff" />
          </g>
          <ellipse cx="25" cy="38" rx="4" ry="2.4" fill="#ffadc9" fill-opacity=".8" />
          <ellipse cx="55" cy="38" rx="4" ry="2.4" fill="#ffadc9" fill-opacity=".8" />
          <path d="M38.6 36.4h2.8l-1.4 1.6z" fill="#e2668f" />
          <path d="M36.5 39c1.2 1.4 2.6 1.4 3.5 0 .9 1.4 2.3 1.4 3.5 0" fill="none" stroke="#4a3043" stroke-width="1.3" stroke-linecap="round" />
          <ellipse cx="31" cy="66" rx="6" ry="4" fill="#fff4e8" stroke="#7a5469" stroke-width="2" />
          <ellipse cx="49" cy="66" rx="6" ry="4" fill="#fff4e8" stroke="#7a5469" stroke-width="2" />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.dot { width: 9px; height: 9px; border-radius: 50%; background: var(--ok); flex: none; box-shadow: 0 0 0 3px color-mix(in srgb, var(--ok) 25%, transparent); }
.dot.warn { background: var(--warn); box-shadow: 0 0 0 3px var(--warn-soft); } .dot.bad { background: var(--bad); box-shadow: 0 0 0 3px var(--bad-soft); }
.badge { position: absolute; top: -4px; right: -4px; min-width: 18px; padding: 0 5px; border-radius: 9px; font-size: 10.5px; font-weight: 800; line-height: 18px; text-align: center; color: var(--panel); background: var(--bad); border: 2px solid var(--panel); }
.cm { position: absolute; top: -2px; right: -2px; width: 10px; height: 10px; border-radius: 50%; background: var(--accent); border: 2px solid var(--panel); }
.cm.input { background: var(--warn); }
.cm.busy { animation: kwpulse 1.4s ease-in-out infinite; }
@keyframes kwpulse { 50% { transform: scale(.6); } }
.brand { display: flex; align-items: center; gap: 6px; color: var(--text); font-weight: 800; font-size: 18px; letter-spacing: -.01em; }
.brand:hover { text-decoration: none; }
.heart { color: var(--accent); }
.round { display: grid; place-items: center; width: 38px; height: 38px; border-radius: 50%; border: 2px solid var(--line); background: var(--panel); color: var(--accent); cursor: pointer; box-shadow: 0 3px 0 var(--line); }
.round:active { transform: translateY(2px); box-shadow: 0 1px 0 var(--line); }

/* phone top row */
.top { display: none; }
/* desktop sticker sheet */
.sheet {
  position: fixed; z-index: 60; top: 12px; bottom: 12px; left: 12px; width: 208px; display: flex; flex-direction: column; gap: 12px;
  padding: 18px 14px 96px; border-radius: 26px; border: 2px dashed color-mix(in srgb, var(--accent) 30%, transparent);
  background:
    radial-gradient(circle, color-mix(in srgb, var(--accent) 14%, transparent) 1.2px, transparent 1.6px) 0 0 / 16px 16px,
    color-mix(in srgb, var(--panel) 80%, transparent);
  box-shadow: 0 10px 30px rgba(214, 69, 140, .12);
}
.sheet .brand { padding: 0 6px; }
.find { display: flex; align-items: center; gap: 8px; min-height: 36px; padding: 0 14px; border-radius: 999px; font: inherit; font-weight: 700; color: var(--muted); background: var(--panel); border: 2px solid var(--line); cursor: pointer; }
.find:hover { color: var(--accent); }
.jobs:empty { display: none; }
.stickers { flex: 1; min-height: 0; overflow-y: auto; display: flex; flex-direction: column; gap: 9px; padding: 6px 6px 10px; scrollbar-width: thin; }
.sticker {
  position: relative; display: flex; align-items: center; gap: 10px; min-height: 42px; padding: 5px 12px 5px 6px; border-radius: 16px;
  color: var(--text); font-weight: 700; background: var(--panel); border: 3px solid var(--panel);
  box-shadow: 0 2px 0 var(--line-2), 0 6px 12px rgba(214, 69, 140, .12);
  transform: rotate(var(--tilt)); transition: transform .35s cubic-bezier(.34, 1.56, .64, 1), background .2s;
}
.sticker:hover, .sticker.on { transform: rotate(0deg) scale(1.04); text-decoration: none; }
.sticker.on { background: color-mix(in srgb, var(--accent) 13%, var(--panel)); color: var(--accent); }
.si { flex: none; display: grid; place-items: center; width: 30px; height: 30px; border-radius: 50%; color: var(--text); }
.sl { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sticker .bow { position: absolute; top: -9px; left: 50%; transform: translateX(-50%) rotate(-8deg); }
.foot { padding: 0 8px; font-size: 12px; color: var(--faint); font-weight: 700; }

/* phone bubble bar */
.bubbles, .kscrim { display: none; }

/* the cat */
.mascot { position: fixed; z-index: 63; left: 40px; bottom: 18px; width: 80px; display: flex; flex-direction: column; align-items: center; }
.cat { display: block; padding: 0; background: none; border: 0; cursor: pointer; -webkit-tap-highlight-color: transparent; filter: drop-shadow(0 4px 4px rgba(122, 84, 105, .25)); }
.cat svg { display: block; overflow: visible; }
.cat:active { transform: scale(.95); }
.eyes { transform-box: fill-box; transform-origin: center; animation: kwblink 5.2s infinite; }
.tail { transform-box: fill-box; transform-origin: 0% 100%; animation: kwtail 2.4s ease-in-out infinite alternate; }
.hop .cat { animation: kwhop .62s cubic-bezier(.34, 1.56, .64, 1); }
.paused .eyes, .paused .tail { animation-play-state: paused; }
.bubble {
  position: absolute; bottom: calc(100% + 6px); left: 0; width: max-content; max-width: 190px; padding: 8px 12px; border-radius: 16px;
  font-size: 13.5px; font-weight: 800; color: var(--text); background: var(--panel); border: 2px solid var(--line-2); box-shadow: 0 6px 16px rgba(214, 69, 140, .18);
}
.bubble::after { content: ""; position: absolute; top: 100%; left: 30px; border: 8px solid transparent; border-top-color: var(--line-2); }
.pop { position: absolute; left: 50%; top: 18px; color: var(--accent); font-size: 18px; pointer-events: none; opacity: 0; animation: kwheart 1.1s ease-out forwards; }
.kw-say-enter-active { animation: kwpopin .4s cubic-bezier(.34, 1.56, .64, 1); }
.kw-say-leave-active { transition: opacity .2s, transform .2s; }
.kw-say-leave-to { opacity: 0; transform: translateY(4px); }
@keyframes kwblink { 0%, 90%, 100% { transform: scaleY(1); } 93% { transform: scaleY(.12); } 96% { transform: scaleY(1); } }
@keyframes kwtail { from { transform: rotate(-6deg); } to { transform: rotate(8deg); } }
@keyframes kwhop { 0% { transform: translateY(0) scale(1, 1); } 25% { transform: translateY(0) scale(1.1, .88); } 55% { transform: translateY(-16px) scale(.94, 1.08); } 80% { transform: translateY(0) scale(1.08, .92); } 100% { transform: translateY(0) scale(1, 1); } }
@keyframes kwheart { 0% { opacity: 0; transform: translate(-50%, 0) scale(.4); } 20% { opacity: 1; } 100% { opacity: 0; transform: translate(calc(-50% + var(--x)), -70px) rotate(var(--r)) scale(1.2); } }
@keyframes kwpopin { 0% { opacity: 0; transform: scale(.5) translateY(8px); } 100% { opacity: 1; transform: none; } }
@keyframes kwjelly { 0% { transform: scale(1, 1); } 30% { transform: scale(1.18, .84); } 50% { transform: scale(.88, 1.12); } 70% { transform: scale(1.06, .95); } 100% { transform: scale(1, 1); } }

/* tablet: icon-only stickers */
@media (max-width: 900px) and (min-width: 641px) {
  .sheet { width: 76px; padding: 14px 8px 86px; align-items: center; }
  .bl, .upt { display: none; }
  .sheet .brand { padding: 0; }
  .find { width: 42px; padding: 0; justify-content: center; }
  .sticker { padding: 4px; min-height: 0; }
  .mascot { left: 8px; width: 72px; }
}

@media (max-width: 640px) {
  .sheet { display: none; }
  .top { display: flex; align-items: center; gap: 8px; padding: calc(env(safe-area-inset-top, 0px) + 8px) 12px 0 16px; }
  .top .brand { margin-right: auto; }
  .upt { font-size: 12px; font-weight: 700; color: var(--faint); }
  .bubbles {
    position: fixed; z-index: 60; left: 10px; right: 10px; bottom: calc(10px + env(safe-area-inset-bottom)); height: 62px; display: flex; align-items: center;
    border-radius: 31px; background: color-mix(in srgb, var(--panel) 92%, transparent); border: 2px solid var(--line);
    box-shadow: 0 8px 24px rgba(214, 69, 140, .2), inset 0 -3px 0 color-mix(in srgb, var(--line) 70%, transparent);
    backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  }
  .strip { flex: 1; min-width: 0; height: 100%; display: flex; align-items: center; gap: 4px; padding: 0 8px; overflow-x: auto; scrollbar-width: none; }
  .strip::-webkit-scrollbar { display: none; }
  .catslot { flex: none; width: 74px; }
  .bub { position: relative; flex: none; display: flex; align-items: center; gap: 6px; height: 46px; padding: 0 4px; border-radius: 23px; color: var(--muted); -webkit-tap-highlight-color: transparent; }
  .bub:hover { text-decoration: none; }
  .bi { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 50%; transition: background .2s; }
  .bub:active .bi { animation: kwjelly .45s; }
  .bub.on { color: var(--text); padding-right: 12px; background: color-mix(in srgb, var(--accent) 10%, transparent); animation: kwjelly .55s; }
  .bl2 { font-weight: 800; font-size: 13px; white-space: nowrap; max-width: 110px; overflow: hidden; text-overflow: ellipsis; }
  .bub .bow { position: absolute; top: -3px; left: 24px; transform: translateX(-50%) rotate(-10deg); }
  .bub .badge { top: 0; right: auto; left: 28px; }
  .bub .cm { top: 3px; right: auto; left: 32px; }
  button.bub { border: 0; background: none; font: inherit; cursor: pointer; }
  button.bub.on { background: color-mix(in srgb, var(--accent) 10%, transparent); }
  .kscrim { display: flex; align-items: flex-end; position: fixed; inset: 0; z-index: 59; padding: 0 10px calc(84px + env(safe-area-inset-bottom)); background: color-mix(in srgb, var(--text) 18%, transparent); }
  .kmore { width: 100%; max-height: 70dvh; display: flex; flex-direction: column; border-radius: 26px; background: var(--panel); border: 2px solid var(--line); box-shadow: 0 10px 30px rgba(214, 69, 140, .22); }
  .khead { display: flex; align-items: center; gap: 8px; padding: 12px 12px 6px 18px; }
  .khead b { flex: 1; min-width: 0; font-size: 13.5px; color: var(--muted); }
  .kedit { min-height: 36px; padding: 0 14px; border-radius: 999px; border: 2px solid var(--line); background: var(--panel); color: var(--accent); font: inherit; font-weight: 800; cursor: pointer; box-shadow: 0 3px 0 var(--line); }
  .kedit.on { background: var(--accent); border-color: var(--accent); color: var(--panel); box-shadow: 0 3px 0 color-mix(in srgb, var(--accent) 60%, var(--text)); }
  .kgrid { overflow-y: auto; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; padding: 6px 12px 14px; }
  .kpage { position: relative; display: flex; flex-direction: column; align-items: center; gap: 4px; min-height: 76px; padding: 8px 4px; border-radius: 20px; border: 2px solid transparent; background: none; color: var(--text); font: inherit; font-weight: 700; font-size: 12px; cursor: pointer; -webkit-tap-highlight-color: transparent; }
  .kpage .si { width: 40px; height: 40px; }
  .kpage:active .si { animation: kwjelly .45s; }
  .kpage.on, .kpage.pinned { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, transparent); }
  .kpage.dim { opacity: .4; }
  .kl { max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .kpin { position: absolute; top: 4px; right: 8px; color: var(--accent); font-size: 15px; }
  .kpage .badge, .kpage .cm { top: 4px; right: 10px; }
  .mascot { left: auto; right: 14px; bottom: calc(16px + env(safe-area-inset-bottom)); width: 72px; }
  .cat svg { width: 66px; height: 60px; }
  .bubble { left: auto; right: 0; max-width: min(230px, calc(100vw - 40px)); }
  .bubble::after { left: auto; right: 26px; }
}

@media (prefers-reduced-motion: reduce) {
  .eyes, .tail, .hop .cat, .bub.on, .bub:active .bi, .kpage:active .si, .cm.busy, .kw-say-enter-active { animation: none; }
  .sticker { transition: none; }
  .pop { animation: none; opacity: 0; }
}
</style>

<style>
/* room for the sidebar (desktop) and the floating bubble bar (phone); only while this skin is on */
@media (min-width: 901px) { html.skin-kawaii .shell.skinned { padding-left: 232px; } }
@media (max-width: 900px) and (min-width: 641px) { html.skin-kawaii .shell.skinned { padding-left: 98px; } }
@media (min-width: 641px) { html.skin-kawaii main.wrap { padding-bottom: 60px; } }
@media (max-width: 640px) {
  html.skin-kawaii .shell.skinned { --tabbar: calc(86px + env(safe-area-inset-bottom)); }
  html.skin-kawaii main.wrap { padding-bottom: calc(100px + env(safe-area-inset-bottom)); }
  html.skin-kawaii.kb .kw-nav .bubbles, html.skin-kawaii.kb .kw-nav .mascot { display: none; }
}
/* soft, round, chunky icons with a pastel tint */
html.skin-kawaii svg.icon { stroke-width: 2.3; stroke-linecap: round; stroke-linejoin: round; fill: color-mix(in srgb, currentColor 16%, transparent); }
/* page change: a bouncy pop */
html.skin-kawaii .skin-kawaii-enter-active { animation: kw-page-pop .34s cubic-bezier(.34, 1.56, .64, 1); }
html.skin-kawaii .skin-kawaii-leave-active { transition: opacity .12s, transform .12s; }
html.skin-kawaii .skin-kawaii-leave-to { opacity: 0; transform: scale(.97); }
@keyframes kw-page-pop { 0% { opacity: 0; transform: scale(.92); } 100% { opacity: 1; transform: scale(1); } }
@media (prefers-reduced-motion: reduce) {
  html.skin-kawaii .skin-kawaii-enter-active { animation: none; }
  html.skin-kawaii .skin-kawaii-leave-active { transition: none; }
}
</style>
