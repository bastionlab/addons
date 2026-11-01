<script setup lang="ts">
/**
 * Disco navigation. Desktop: a jukebox on the left: chrome arch with glowing tubes, a "now playing" strip with the
 * current page on a spinning single, every page a song card ("A1 Home", "A2 Metrics", …), a coin-slot footer with
 * the live state. Narrow desktop: the same jukebox slimmed to codes + icons. Phone: a compact neon top strip and a
 * bottom bar of the viewer's pinned pages (useNavPins) where the open page's icon sits on a spinning vinyl record,
 * + "more": a sheet with every page as a song card and "edit tabs" to pick the pinned ones.
 * Also owns the confetti (tap any .btn → a small burst at the pointer) and the "Party mode!" line the Backdrop's
 * mirror-ball easter egg switches on.
 */
const props = withDefaults(defineProps<{
  nav?: { to: string, icon: string, label: string }[], path?: string
  badge?: (to: string) => number, mark?: (to: string) => string
  state?: string, stateText?: string, up?: string, full?: boolean
}>(), { nav: () => [], path: '/', badge: () => 0, mark: () => '', state: 'ok', stateText: '', up: '', full: false })
const emit = defineEmits<{ search: [] }>()
const party = useState('skinDisco:party', () => false)

const code = (i: number) => `${'ABCDEFGH'[Math.floor(i / 9)] ?? 'Z'}${(i % 9) + 1}`
const here = computed(() => {
  const i = props.nav.findIndex(n => n.to === props.path)
  return i < 0 ? null : { ...props.nav[i]!, code: code(i) }
})

// keep the current record in view on the phone bar
const bar = ref<HTMLElement | null>(null)
function centre() {
  const b = bar.value
  const on = b?.querySelector<HTMLElement>('.vt.on')
  if (!b || !on) return
  b.scrollTo({ left: on.offsetLeft - (b.clientWidth - on.offsetWidth) / 2, behavior: 'smooth' })
}
watch(() => props.path, () => { sheet.value = false; nextTick(centre) })

// phone bar: pinned pages + the open one if unpinned + "more" (sheet with every page; edits the pins)
const pins = useNavPins(() => props.nav)
const { editing } = pins
const sheet = ref(false)
const offTab = computed(() => props.nav.find(n => n.to === props.path && !pins.isPinned(n.to)) ?? null)
const moreBadge = computed(() => props.nav.filter(n => !pins.isPinned(n.to)).reduce((s, n) => s + props.badge(n.to), 0))
watch(sheet, v => { if (!v) editing.value = false })
function pick(to: string) { if (editing.value) pins.toggle(to); else { sheet.value = false; if (to !== props.path) navigateTo(to) } }
const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') sheet.value = false }

// confetti: a little burst at the pointer on every .btn tap, only while this skin is mounted
type Bit = { k: number, dx: number, dy: number, r: number, c: string, w: number, h: number, round: boolean }
type Burst = { id: number, x: number, y: number, bits: Bit[] }
const bursts = ref<Burst[]>([])
const COLOURS = ['#ff3fb4', '#3fd8ff', '#ffc93f', '#b44bff', '#3ff2a0', '#ffffff']
let seq = 0
let reduced = false
const timers = new Set<ReturnType<typeof setTimeout>>()
function onDown(e: PointerEvent) {
  if (reduced) return
  const el = (e.target as Element | null)?.closest?.('.btn')
  if (!el || (el as HTMLButtonElement).disabled) return
  const id = ++seq
  const bits: Bit[] = Array.from({ length: 14 }, (_, k) => {
    const a = (k / 14) * Math.PI * 2 + Math.random() * 0.4
    const d = 34 + Math.random() * 38
    return {
      k, dx: Math.cos(a) * d, dy: Math.sin(a) * d - 18, r: Math.round(Math.random() * 540 - 270),
      c: COLOURS[(k + id) % COLOURS.length]!, w: 5 + Math.round(Math.random() * 3), h: 3 + Math.round(Math.random() * 6), round: k % 4 === 0,
    }
  })
  bursts.value = [...bursts.value.slice(-3), { id, x: e.clientX, y: e.clientY, bits }]
  const tm = setTimeout(() => { bursts.value = bursts.value.filter(b => b.id !== id); timers.delete(tm) }, 900)
  timers.add(tm)
}
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
  <div class="disco-nav" :class="{ full, party }">
    <!-- ---------- desktop jukebox ---------- -->
    <aside class="jbox" :aria-label="$t('skinDisco.jukebox')">
      <div class="arch">
        <svg viewBox="0 0 220 112" preserveAspectRatio="xMidYMax meet" aria-hidden="true">
          <defs>
            <linearGradient id="skin-disco-chrome" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stop-color="#f6f2ff" /><stop offset=".3" stop-color="#8d84a8" />
              <stop offset=".55" stop-color="#ffffff" /><stop offset=".8" stop-color="#6c6488" /><stop offset="1" stop-color="#d9d3ec" />
            </linearGradient>
            <linearGradient id="skin-disco-tube" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stop-color="#ff3fb4" /><stop offset=".25" stop-color="#ffc93f" /><stop offset=".5" stop-color="#3ff2a0" />
              <stop offset=".75" stop-color="#3fd8ff" /><stop offset="1" stop-color="#b44bff" />
            </linearGradient>
          </defs>
          <path d="M6 112 V64 A104 60 0 0 1 214 64 V112 Z" fill="url(#skin-disco-chrome)" />
          <path d="M16 112 V66 A94 52 0 0 1 204 66 V112 Z" fill="#1b0f30" />
          <path class="tube t1" d="M24 112 V68 A86 46 0 0 1 196 68 V112" fill="none" stroke="url(#skin-disco-tube)" stroke-width="5" stroke-linecap="round" />
          <path class="tube t2" d="M36 112 V72 A74 38 0 0 1 184 72 V112" fill="none" stroke="#ff3fb4" stroke-width="3" stroke-linecap="round" />
          <path class="tube t3" d="M48 112 V76 A62 30 0 0 1 172 76 V112" fill="none" stroke="#3fd8ff" stroke-width="3" stroke-linecap="round" />
          <g fill="#ffe9a8">
            <circle class="bub b1" cx="24" cy="98" r="2" /><circle class="bub b2" cx="196" cy="92" r="2" /><circle class="bub b3" cx="24" cy="84" r="1.6" />
          </g>
        </svg>
        <NuxtLink to="/" class="brand" :aria-label="'bastion'"><span class="bn">{{ 'bastion' }}</span><i class="sd" :class="state" /></NuxtLink>
      </div>

      <div class="np" :title="stateText">
        <span class="single" aria-hidden="true"><i /></span>
        <span class="npt">
          <small>{{ $t('skinDisco.playing') }}</small>
          <span class="scroll"><b>{{ here ? `${here.code} · ${here.label}` : 'bastion' }}</b></span>
        </span>
      </div>

      <nav class="songs">
        <NuxtLink v-for="(n, i) in nav" :key="n.to" :to="n.to" class="song" :class="{ on: n.to === path }" :title="n.label">
          <span class="code">{{ code(i) }}</span>
          <Icon :name="n.icon" :size="17" class="si" />
          <span class="sl">{{ n.label }}</span>
          <span v-if="badge(n.to)" class="bdg">{{ badge(n.to) }}</span>
          <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
          <span v-if="n.to === path" class="eqm" aria-hidden="true"><i /><i /><i /></span>
        </NuxtLink>
      </nav>

      <div class="foot">
        <button type="button" class="find" @click="emit('search')"><Icon name="search" :size="16" /><span class="fl">{{ $t('skinDisco.search') }}</span></button>
        <JobsButton />
        <div class="coin" :class="state" :title="stateText">
          <span class="slot" aria-hidden="true" />
          <span class="ct"><small>{{ $t('skinDisco.coin') }}</small><b>{{ up }} · {{ stateText }}</b></span>
        </div>
      </div>
    </aside>

    <!-- ---------- phone: neon top strip + vinyl bottom bar ---------- -->
    <header class="pt-top">
      <NuxtLink to="/" class="pbrand" :aria-label="'bastion'"><span class="bn">{{ 'bastion' }}</span><i class="sd" :class="state" /></NuxtLink>
      <span class="ptools">
        <JobsButton />
        <button type="button" class="pfind" :aria-label="$t('skinDisco.search')" @click="emit('search')"><Icon name="search" :size="20" /></button>
      </span>
    </header>

    <nav ref="bar" class="vbar" :aria-label="$t('skinDisco.pages')">
      <NuxtLink v-for="n in [...pins.pinned.value, ...(offTab ? [offTab] : [])]" :key="n.to" :to="n.to" class="vt" :class="{ on: n.to === path && !sheet }">
        <span class="disc" aria-hidden="true"><i /></span>
        <span class="vi"><Icon :name="n.icon" :size="22" /></span>
        <span class="vl">{{ n.label }}</span>
        <span v-if="badge(n.to)" class="bdg">{{ badge(n.to) }}</span>
        <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
      </NuxtLink>
      <button type="button" class="vt vmore" :class="{ on: sheet }" :aria-expanded="sheet" @click="sheet = !sheet">
        <span class="disc" aria-hidden="true"><i /></span>
        <span class="vi"><Icon name="grid" :size="22" /></span>
        <span class="vl">{{ $t('skinDisco.more') }}</span>
        <span v-if="moreBadge" class="bdg">{{ moreBadge }}</span>
      </button>
    </nav>

    <Transition name="dsheet">
      <div v-if="sheet" class="dscrim" @click.self="sheet = false">
        <div class="dsheet" role="dialog" :aria-label="$t('skinDisco.pages')">
          <div class="dhead">
            <span class="dh">{{ editing ? $t('skinDisco.pinCount', { n: pins.keys.value.length, max: pins.max }) : $t('skinDisco.tracks', { n: nav.length }) }}</span>
            <button type="button" class="dedit" :class="{ on: editing }" :aria-pressed="editing" @click="editing = !editing">{{ editing ? $t('skinDisco.done') : $t('skinDisco.editTabs') }}</button>
          </div>
          <div class="dlist">
            <button v-for="(n, i) in nav" :key="n.to" type="button" class="song"
              :class="{ on: editing ? pins.isPinned(n.to) : n.to === path, dim: editing && pins.full.value && !pins.isPinned(n.to) }"
              :aria-pressed="editing ? pins.isPinned(n.to) : undefined" @click="pick(n.to)">
              <span class="code">{{ code(i) }}</span>
              <Icon :name="n.icon" :size="17" class="si" />
              <span class="sl">{{ n.label }}</span>
              <Icon v-if="editing && pins.isPinned(n.to)" name="pin" :size="15" class="si" />
              <span v-else-if="badge(n.to)" class="bdg">{{ badge(n.to) }}</span>
              <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="dparty">
      <div v-if="party" class="party-line" role="status">{{ $t('skinDisco.party') }}</div>
    </Transition>

    <div class="fx" aria-hidden="true">
      <div v-for="b in bursts" :key="b.id" class="burst" :style="{ left: `${b.x}px`, top: `${b.y}px` }">
        <i
          v-for="p in b.bits" :key="p.k" class="bit" :class="{ round: p.round }"
          :style="{ '--dx': `${p.dx}px`, '--dy': `${p.dy}px`, '--r': `${p.r}deg`, background: p.c, width: `${p.w}px`, height: `${p.h}px` }"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ---------- jukebox ---------- */
.jbox {
  position: fixed; z-index: 50; left: 10px; top: 10px; bottom: 10px; width: calc(var(--disco-side, 236px) - 20px);
  display: flex; flex-direction: column; gap: 10px; padding: 0 12px 12px;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, .06), rgba(255, 255, 255, 0) 12%, rgba(255, 255, 255, 0) 88%, rgba(255, 255, 255, .06)),
    linear-gradient(180deg, rgba(60, 24, 40, 1), rgba(34, 12, 28, 1));
  border: 3px solid rgba(214, 206, 236, .75); border-top: 0; border-radius: 0 0 22px 22px;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, .5), 0 0 30px rgba(255, 63, 180, .25), inset 0 0 22px rgba(0, 0, 0, .6);
}
.arch { position: relative; margin: 0 -15px; flex: none; }
.arch svg { display: block; width: 100%; height: auto; }
.tube { filter: drop-shadow(0 0 4px rgba(255, 255, 255, .5)); animation: tube 3s ease-in-out infinite; }
.t2 { animation-delay: .5s; } .t3 { animation-delay: 1s; }
@keyframes tube { 0%, 100% { opacity: 1; } 50% { opacity: .55; } }
.bub { animation: bubble 4s linear infinite; }
.b2 { animation-delay: 1.3s; } .b3 { animation-delay: 2.6s; }
@keyframes bubble { from { transform: translateY(0); opacity: 1; } to { transform: translateY(-40px); opacity: 0; } }
.brand { position: absolute; left: 0; right: 0; bottom: 6px; display: flex; justify-content: center; align-items: center; gap: 6px; text-decoration: none; }
.brand:hover, .pbrand:hover { text-decoration: none; }
.bn {
  font-size: 22px; font-weight: 900; font-style: italic; letter-spacing: .02em; color: var(--text);
  text-shadow: 0 0 6px rgba(255, 63, 180, .95), 0 0 16px rgba(255, 63, 180, .6);
}
.sd { width: 9px; height: 9px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 8px var(--ok); }
.sd.warn { background: var(--warn); box-shadow: 0 0 8px var(--warn); }
.sd.bad { background: var(--bad); box-shadow: 0 0 8px var(--bad); }

.np {
  display: flex; align-items: center; gap: 10px; padding: 8px 10px; flex: none;
  background: rgba(10, 4, 20, .85); border: 1.5px solid rgba(255, 201, 63, .55); border-radius: 10px;
  box-shadow: inset 0 0 12px rgba(255, 201, 63, .15);
}
.single, .disc {
  position: relative; flex: none; width: 34px; height: 34px; border-radius: 50%;
  background: repeating-radial-gradient(circle, rgba(20, 14, 30, 1) 0 1.5px, rgba(48, 40, 62, 1) 2px 2.6px);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, .15);
  animation: dspin 1.8s linear infinite;
}
.single::after, .disc::after { content: ''; position: absolute; left: 22%; top: 18%; width: 30%; height: 18%; border-radius: 50%; background: rgba(255, 255, 255, .22); transform: rotate(-30deg); }
.single i, .disc i { position: absolute; inset: 32%; border-radius: 50%; background: conic-gradient(var(--accent) 0 50%, var(--warn) 0); }
.single i::after, .disc i::after { content: ''; position: absolute; inset: 40%; border-radius: 50%; background: rgba(10, 4, 20, 1); }
@keyframes dspin { to { transform: rotate(360deg); } }
.npt { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.npt small { font-size: 9.5px; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; color: var(--warn); }
.scroll { overflow: hidden; white-space: nowrap; }
.scroll b { display: inline-block; font-size: 13.5px; color: var(--text); padding-right: 20px; }

.songs { flex: 1; min-height: 0; overflow-y: auto; display: flex; flex-direction: column; gap: 5px; padding: 2px; scrollbar-width: thin; }
.song {
  position: relative; display: flex; align-items: center; gap: 8px; min-height: 36px; padding: 4px 8px 4px 4px; flex: none;
  color: var(--text); text-decoration: none; font-size: 13.5px; font-weight: 700;
  background: linear-gradient(180deg, rgba(255, 249, 232, .96), rgba(240, 228, 205, .96));
  border-radius: 5px; box-shadow: 0 1px 0 rgba(0, 0, 0, .4); transition: transform .15s;
}
.song .sl, .song .si { color: rgba(40, 18, 46, 1); }
.song::before { content: ''; position: absolute; left: 40px; right: 6px; top: 50%; height: 0; border-top: 1px dashed rgba(180, 60, 110, .25); pointer-events: none; }
.song:hover { text-decoration: none; transform: translateX(3px); }
.code {
  flex: none; width: 30px; height: 28px; display: grid; place-items: center; border-radius: 4px;
  font-size: 12px; font-weight: 900; color: var(--text); background: rgba(150, 30, 90, 1);
}
.sl { position: relative; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; background: inherit; padding-right: 4px; }
.si { position: relative; flex: none; }
.song.on { background: linear-gradient(90deg, rgba(255, 63, 180, 1), rgba(180, 75, 255, 1)); box-shadow: 0 0 16px rgba(255, 63, 180, .6); transform: translateX(4px); }
.song.on .sl, .song.on .si { color: var(--text); }
.song.on .sl { background: none; }
.song.on .code { background: rgba(255, 249, 232, 1); color: rgba(150, 30, 90, 1); }
.song.on::before { display: none; }
.eqm { display: flex; align-items: flex-end; gap: 2px; height: 14px; flex: none; }
.eqm i { width: 3px; height: 100%; background: var(--text); transform-origin: bottom; animation: eq .7s ease-in-out infinite alternate; }
.eqm i:nth-child(2) { animation-duration: .5s; } .eqm i:nth-child(3) { animation-duration: .85s; }
@keyframes eq { from { transform: scaleY(.25); } to { transform: scaleY(1); } }
.bdg { flex: none; min-width: 18px; padding: 0 5px; font-size: 11px; font-weight: 900; line-height: 18px; text-align: center; color: var(--text); background: var(--bad); border-radius: 999px; box-shadow: 0 0 8px var(--bad); }
.cm { flex: none; width: 10px; height: 10px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 8px var(--accent); }
.cm.busy { animation: blink 1.1s ease-in-out infinite; }
.cm.input { background: var(--warn); box-shadow: 0 0 8px var(--warn); }
@keyframes blink { 50% { opacity: .25; } }

.foot { flex: none; display: flex; flex-direction: column; gap: 8px; }
.find {
  display: flex; align-items: center; justify-content: center; gap: 8px; min-height: 36px; font: inherit; font-weight: 800; font-size: 13px; letter-spacing: .06em; text-transform: uppercase;
  color: var(--text); background: rgba(10, 4, 20, .7); border: 1.5px solid rgba(63, 216, 255, .6); border-radius: 999px; cursor: pointer;
  box-shadow: 0 0 10px rgba(63, 216, 255, .25);
}
.find:hover { box-shadow: 0 0 16px rgba(63, 216, 255, .55); }
.coin { display: flex; align-items: center; gap: 10px; padding: 6px 10px; background: rgba(214, 206, 236, .12); border: 1.5px solid rgba(214, 206, 236, .4); border-radius: 8px; }
.slot { flex: none; width: 6px; height: 26px; border-radius: 3px; background: rgba(0, 0, 0, .8); box-shadow: 0 0 0 2px rgba(214, 206, 236, .6), 0 0 10px var(--ok); }
.coin.warn .slot { box-shadow: 0 0 0 2px rgba(214, 206, 236, .6), 0 0 10px var(--warn); }
.coin.bad .slot { box-shadow: 0 0 0 2px rgba(214, 206, 236, .6), 0 0 10px var(--bad); }
.ct { display: flex; flex-direction: column; min-width: 0; }
.ct small { font-size: 9px; letter-spacing: .14em; text-transform: uppercase; color: var(--faint); }
.ct b { font-size: 12px; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.disco-nav :deep(.jt) { justify-content: center; border-color: rgba(255, 201, 63, .6); background: rgba(10, 4, 20, .7); color: var(--text); }

/* slim jukebox: codes + icons */
@media (min-width: 641px) and (max-width: 960px) {
  .jbox { padding: 0 8px 10px; }
  .bn { font-size: 13px; }
  .np { justify-content: center; padding: 6px; }
  .npt, .sl, .song::before, .eqm, .fl, .ct, .disco-nav :deep(.jt .l) { display: none; }
  .song { flex-direction: column; gap: 2px; padding: 4px; min-height: 52px; }
  .song .bdg, .song .cm { position: absolute; top: 2px; right: 2px; }
  .code { width: 100%; height: 20px; font-size: 11px; }
  .coin { justify-content: center; padding: 6px; }
}

/* ---------- phone ---------- */
.pt-top, .vbar { display: none; }
.pt-top {
  position: relative; z-index: 5; align-items: center; justify-content: space-between; gap: 10px;
  height: 56px; padding: calc(env(safe-area-inset-top, 0px) + 6px) 12px 0;
}
.pbrand { display: flex; align-items: center; gap: 6px; text-decoration: none; }
.pbrand .bn { font-size: 20px; }
.ptools { display: flex; align-items: center; gap: 8px; }
.pfind {
  display: grid; place-items: center; width: 40px; height: 40px; padding: 0; color: var(--text); cursor: pointer;
  background: rgba(10, 4, 20, .7); border: 1.5px solid rgba(63, 216, 255, .6); border-radius: 50%; box-shadow: 0 0 10px rgba(63, 216, 255, .3);
}
.vbar {
  position: fixed; z-index: 60; left: 0; right: 0; bottom: 0; gap: 2px; align-items: flex-end; overflow-x: auto; scrollbar-width: none;
  height: calc(70px + env(safe-area-inset-bottom)); padding: 0 8px env(safe-area-inset-bottom);
  background: linear-gradient(180deg, rgba(30, 14, 52, .96), rgba(12, 5, 24, .98));
  box-shadow: 0 -10px 30px rgba(0, 0, 0, .45);
}
.vbar::before {
  content: ''; position: fixed; left: 0; right: 0; bottom: calc(70px + env(safe-area-inset-bottom)); height: 3px;
  background: linear-gradient(90deg, rgba(255, 63, 180, 1), rgba(255, 201, 63, 1), rgba(63, 242, 160, 1), rgba(63, 216, 255, 1), rgba(180, 75, 255, 1), rgba(255, 63, 180, 1));
  box-shadow: 0 0 12px rgba(255, 63, 180, .6);
}
.vbar::-webkit-scrollbar { display: none; }
.vt {
  position: relative; flex: none; width: 62px; height: 66px; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; gap: 3px; padding-bottom: 7px;
  color: var(--muted); text-decoration: none; -webkit-tap-highlight-color: transparent;
}
.vt:hover { text-decoration: none; }
.vmore { background: none; border: 0; font: inherit; cursor: pointer; }
.dscrim { position: fixed; inset: 0; z-index: 59; background: rgba(10, 4, 20, .55); }
.dsheet {
  position: absolute; left: 8px; right: 8px; bottom: calc(76px + env(safe-area-inset-bottom)); max-height: calc(100dvh - 150px); display: flex; flex-direction: column;
  padding: 10px; background: linear-gradient(180deg, rgba(60, 24, 40, 1), rgba(34, 12, 28, 1)); border: 2px solid rgba(214, 206, 236, .75); border-radius: 18px;
  box-shadow: 0 0 24px rgba(255, 63, 180, .35);
}
.dhead { display: flex; align-items: center; gap: 8px; padding: 0 2px 8px; }
.dh { flex: 1; font-size: 12px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; color: var(--warn); }
.dedit { min-height: 34px; padding: 0 14px; font: inherit; font-weight: 800; font-size: 12.5px; color: var(--text); background: rgba(150, 30, 90, 1); border: 1.5px solid rgba(255, 249, 232, .7); border-radius: 999px; cursor: pointer; }
.dedit.on { background: linear-gradient(90deg, rgba(255, 63, 180, 1), rgba(180, 75, 255, 1)); }
.dlist { overflow-y: auto; display: flex; flex-direction: column; gap: 5px; padding: 2px; }
.dlist .song { min-height: 42px; border: 0; font: inherit; font-weight: 700; text-align: left; cursor: pointer; }
.dlist .song.dim { opacity: .45; }
.dsheet-enter-active, .dsheet-leave-active { transition: opacity .2s; }
.dsheet-enter-active .dsheet { transition: transform .25s cubic-bezier(.3, 1.5, .5, 1); }
.dsheet-enter-from, .dsheet-leave-to { opacity: 0; }
.dsheet-enter-from .dsheet { transform: translateY(24px) scale(.96); }
.vi { position: relative; z-index: 1; display: grid; place-items: center; width: 34px; height: 34px; border-radius: 50%; transition: transform .25s cubic-bezier(.3, 1.6, .5, 1); }
.vl { position: relative; z-index: 1; max-width: 60px; font-size: 10.5px; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vt .disc { position: absolute; left: 50%; top: -8px; width: 54px; height: 54px; margin-left: -27px; opacity: 0; transform: scale(.4); transition: opacity .2s, transform .3s cubic-bezier(.3, 1.6, .5, 1); animation-duration: 2.4s; }
.vt.on { color: var(--text); }
.vt.on .disc { opacity: 1; transform: scale(1); }
.vt.on .vi { transform: translateY(-12px); color: var(--text); background: rgba(150, 30, 90, 1); box-shadow: 0 0 0 2px rgba(255, 249, 232, .85), 0 0 14px rgba(255, 63, 180, .8); }
.vt.on .vl { color: var(--warn); }
.vt .bdg, .vt .cm { position: absolute; z-index: 2; top: 4px; right: 6px; }

/* party line */
.party-line {
  position: fixed; z-index: 96; left: calc(50% + var(--disco-side, 0px) / 2); top: calc(var(--disco-ball-y, 62px) + var(--disco-ball, 64px) / 2 + 14px);
  transform: translateX(-50%); padding: 8px 18px; white-space: nowrap; pointer-events: none;
  font-weight: 900; font-size: 16px; font-style: italic; letter-spacing: .03em; color: var(--text);
  background: linear-gradient(100deg, rgba(255, 63, 180, 1), rgba(180, 75, 255, 1) 50%, rgba(63, 216, 255, 1));
  border-radius: 999px; box-shadow: 0 0 24px rgba(255, 63, 180, .7);
}
.dparty-enter-active { transition: transform .35s cubic-bezier(.3, 1.6, .5, 1), opacity .2s; }
.dparty-leave-active { transition: opacity .3s; }
.dparty-enter-from { transform: translateX(-50%) scale(.4); opacity: 0; }
.dparty-leave-to { opacity: 0; }
.party .song.on, .party .vt.on .vi { animation: pulse .45s ease-in-out infinite alternate; }
@keyframes pulse { to { box-shadow: 0 0 28px rgba(63, 216, 255, .95); } }

/* confetti */
.fx { position: fixed; inset: 0; z-index: 95; pointer-events: none; overflow: hidden; }
.burst { position: absolute; width: 0; height: 0; }
.bit { position: absolute; left: -3px; top: -3px; border-radius: 1px; animation: confetti .85s cubic-bezier(.15, .7, .4, 1) forwards; }
.bit.round { border-radius: 50%; }
@keyframes confetti {
  0% { transform: translate(0, 0) rotate(0) scale(.6); opacity: 1; }
  70% { opacity: 1; }
  100% { transform: translate(var(--dx), calc(var(--dy) + 40px)) rotate(var(--r)) scale(1); opacity: 0; }
}

@media (max-width: 640px) {
  .jbox { display: none; }
  .pt-top, .vbar { display: flex; }
  .vbar { justify-content: space-around; }
  html.kb .vbar { display: none; }
  .full .pt-top { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  .tube, .bub, .single, .disc, .eqm i, .cm.busy, .party .song.on, .party .vt.on .vi { animation: none !important; }
  .song, .vi, .vt .disc { transition: none; }
}
</style>

<style>
/* room for the jukebox (desktop) and the vinyl bar (phone); only while this skin is on */
@media (min-width: 641px) { html.skin-disco .shell.skinned { padding-left: var(--disco-side); } }
/* icons with a chrome-and-neon sheen; the glow only on desktop (no filters on phone) */
html.skin-disco svg.icon { stroke-width: 2; }
@media (min-width: 641px) and (pointer: fine) {
  html.skin-disco svg.icon { filter: drop-shadow(0 0 2px color-mix(in srgb, currentColor 70%, transparent)) drop-shadow(0 0 5px color-mix(in srgb, currentColor 35%, transparent)); }
}
@media (max-width: 640px) {
  html.skin-disco .shell.skinned { --tabbar: calc(74px + env(safe-area-inset-bottom)); }
  html.skin-disco main.wrap { padding-bottom: calc(var(--tabbar) + 24px); }
}
</style>
