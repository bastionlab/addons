<script setup lang="ts">
/**
 * Blocky navigation: a game HUD at the bottom centre (phone and desktop).
 * - Hotbar: 9 bevelled inventory slots, page icon = item, badge = item count, a busy chat = enchant glint.
 *   The open page's slot gets the thick white frame; on every switch its name floats above the hotbar for 2 s.
 *   Slots 1–4 hold the viewer's pinned pages (useNavPins, set in the inventory's "edit hotbar"), then the rest.
 *   More than 9 pages → the hotbar shows the 9-page "row" holding the open page (the rest stay empty slots).
 * - Above it: hearts from the agent state (10 ok, 5 warn, 1 bad, shaking when low), hunger from the `up` ratio,
 *   and an XP bar that is secretly the clock (level = hour, bar = minutes).
 * - Desktop: keys 1–9 pick a slot, the mouse wheel over the hotbar walks through every page, E opens the inventory
 *   (all ignored while typing). The chest button (and E) opens a GUI window with every page.
 */
const props = withDefaults(defineProps<{
  nav?: { to: string, icon: string, label: string }[], path?: string
  badge?: (to: string) => number, mark?: (to: string) => string
  state?: string, stateText?: string, up?: string, full?: boolean
}>(), { nav: () => [], path: '/', badge: () => 0, mark: () => '', state: 'ok', stateText: '', up: '', full: false })
const emit = defineEmits<{ search: [] }>()

// pinned pages first, so the viewer's picks sit in slots 1–4
const pins = useNavPins(() => props.nav)
const { editing } = pins
const order = computed(() => [...pins.pinned.value, ...props.nav.filter(n => !pins.isPinned(n.to))])
const idx = computed(() => order.value.findIndex(n => n.to === props.path))
const row = ref(0)
watch(idx, i => { if (i >= 0) row.value = Math.floor(i / 9) }, { immediate: true })
const slots = computed(() => Array.from({ length: 9 }, (_, k) => order.value[row.value * 9 + k] ?? null))
const rows = computed(() => Math.max(1, Math.ceil(order.value.length / 9)))

// item name above the hotbar for 2 s after a switch
const here = computed(() => (idx.value >= 0 ? order.value[idx.value]! : null))
const showName = ref(false)
let nameT: ReturnType<typeof setTimeout> | undefined
watch(() => props.path, () => {
  showName.value = !!here.value
  clearTimeout(nameT)
  nameT = setTimeout(() => (showName.value = false), 2000)
})

// hearts / hunger / xp
const hearts = computed(() => (props.state === 'bad' ? 1 : props.state === 'warn' ? 5 : 10))
const hunger = computed(() => {
  const m = /(\d+)\s*\/\s*(\d+)/.exec(props.up ?? '')
  if (!m || !Number(m[2])) return 10
  return Math.max(0, Math.min(10, Math.round((10 * Number(m[1])) / Number(m[2]))))
})
const clock = ref(new Date())
let clockT: ReturnType<typeof setInterval> | undefined
const level = computed(() => clock.value.getHours())
const xp = computed(() => clock.value.getMinutes() / 60)

// inventory window
const inv = ref(false)
watch(() => props.path, () => (inv.value = false))
watch(inv, v => { if (!v) editing.value = false })
function go(to?: string) { if (to && to !== props.path) navigateTo(to) }
function pick(to: string) { if (editing.value) pins.toggle(to); else { inv.value = false; go(to) } }

const typing = (e: Event) => {
  const t = e.target as HTMLElement | null
  return !!t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') { inv.value = false; return }
  if (e.ctrlKey || e.metaKey || e.altKey || typing(e)) return
  if (e.key === 'e' || e.key === 'E') { inv.value = !inv.value; e.preventDefault(); return }
  if (/^[1-9]$/.test(e.key)) {
    const s = slots.value[Number(e.key) - 1]
    if (s) { go(s.to); e.preventDefault() }
  }
}
let wheelAt = 0
function onWheel(e: WheelEvent) {
  const n = order.value.length
  if (!n || Math.abs(e.deltaY) < 1) return
  const now = Date.now()
  if (now - wheelAt < 160) return
  wheelAt = now
  const cur = idx.value < 0 ? 0 : idx.value
  go(order.value[(cur + (e.deltaY > 0 ? 1 : -1) + n) % n]!.to)
}
const bar = ref<HTMLElement | null>(null)
const wheelGuard = (e: WheelEvent) => { e.preventDefault(); onWheel(e) }
onMounted(() => {
  window.addEventListener('keydown', onKey)
  bar.value?.addEventListener('wheel', wheelGuard, { passive: false })
  clockT = setInterval(() => { if (!document.hidden) clock.value = new Date() }, 30000)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  bar.value?.removeEventListener('wheel', wheelGuard)
  clearInterval(clockT)
  clearTimeout(nameT)
})
</script>

<template>
  <div class="blocky-nav" :class="{ full }">
    <!-- pixel sprites, defined once -->
    <svg width="0" height="0" class="defs" aria-hidden="true" shape-rendering="crispEdges">
      <symbol id="skin-blocky-heart" viewBox="0 0 9 9">
        <path d="M1 1h3v1h1V1h3v1h1v3H8v1H7v1H6v1H5v1H4V8H3V7H2V6H1V5H0V2h1z" fill="#000000" />
        <path d="M1 2h2v1h1v1h1V3h1V2h2v3H7v1H6v1H5v1H4V7H3V6H2V5H1z" fill="#e01b1b" />
        <rect x="2" y="2" width="1" height="1" fill="#ffb3b3" />
      </symbol>
      <symbol id="skin-blocky-heart0" viewBox="0 0 9 9">
        <path d="M1 1h3v1h1V1h3v1h1v3H8v1H7v1H6v1H5v1H4V8H3V7H2V6H1V5H0V2h1z" fill="#000000" />
        <path d="M1 2h2v1h1v1h1V3h1V2h2v3H7v1H6v1H5v1H4V7H3V6H2V5H1z" fill="#3a1010" />
      </symbol>
      <symbol id="skin-blocky-food" viewBox="0 0 9 9">
        <path d="M4 0h4v1h1v4H8v1H6v1H4v1H3v1H1V8H0V6h1V5h1V3h1V1h1z" fill="#000000" />
        <path d="M4 1h4v4H7v1H5v1H4V6H3V5H2V3h1V2h1z" fill="#b5652a" />
        <rect x="5" y="2" width="2" height="1" fill="#e09a5a" />
        <path d="M1 6h1v1h1v1H1z" fill="#f2ecdc" />
      </symbol>
      <symbol id="skin-blocky-food0" viewBox="0 0 9 9">
        <path d="M4 0h4v1h1v4H8v1H6v1H4v1H3v1H1V8H0V6h1V5h1V3h1V1h1z" fill="#000000" />
        <path d="M4 1h4v4H7v1H5v1H4V6H3V5H2V3h1V2h1z" fill="#3a2a1a" />
      </symbol>
    </svg>

    <div class="hud" data-skin-bar>
      <Transition name="bkname">
        <div v-if="showName && here" :key="here.to" class="iname">{{ here.label }}</div>
      </Transition>
      <div class="jobs"><JobsButton /></div>

      <div class="stats">
        <span class="hearts" :class="{ low: hearts <= 1 }" role="img" :aria-label="$t('skinBlocky.health', { state: stateText })" :title="stateText">
          <svg v-for="i in 10" :key="i" class="pip" :style="{ animationDelay: `${i * 40}ms` }"><use :href="i <= hearts ? '#skin-blocky-heart' : '#skin-blocky-heart0'" /></svg>
        </span>
        <span class="hunger" role="img" :aria-label="$t('skinBlocky.hunger', { up })" :title="up">
          <svg v-for="i in 10" :key="i" class="pip"><use :href="11 - i <= hunger ? '#skin-blocky-food' : '#skin-blocky-food0'" /></svg>
        </span>
      </div>
      <div class="xp" role="img" :aria-label="$t('skinBlocky.level', { n: level })">
        <i class="xpfill" :style="{ transform: `scaleX(${xp})` }" />
        <b class="lvl">{{ level }}</b>
      </div>

      <div class="barrow">
        <button type="button" class="side find" :aria-label="$t('skinBlocky.search')" @click="emit('search')"><Icon name="search" :size="20" /></button>
        <nav ref="bar" class="hotbar" :aria-label="$t('skinBlocky.hotbar')">
          <template v-for="(s, k) in slots" :key="k">
            <NuxtLink v-if="s" :to="s.to" class="slot" :class="{ on: s.to === path, glint: !!mark(s.to), input: mark(s.to) === 'input' }" :aria-label="s.label" :title="s.label">
              <Icon :name="s.icon" :size="20" class="item" />
              <span v-if="badge(s.to)" class="count">{{ badge(s.to) }}</span>
              <span class="key" aria-hidden="true">{{ k + 1 }}</span>
            </NuxtLink>
            <span v-else class="slot empty" aria-hidden="true" />
          </template>
        </nav>
        <button type="button" class="side chest" :aria-label="$t('skinBlocky.inventory')" :aria-expanded="inv" @click="inv = !inv">
          <svg viewBox="0 0 16 16" shape-rendering="crispEdges" aria-hidden="true">
            <rect x="1" y="3" width="14" height="12" fill="#000000" />
            <rect x="2" y="4" width="12" height="4" fill="#a8742e" /><rect x="2" y="9" width="12" height="5" fill="#8a5a1e" />
            <rect x="2" y="8" width="12" height="1" fill="#3a2410" /><rect x="7" y="7" width="2" height="3" fill="#d8d8d8" />
            <rect x="3" y="5" width="4" height="1" fill="#c9924a" />
          </svg>
          <span v-if="rows > 1" class="rowtag">{{ row + 1 }}/{{ rows }}</span>
        </button>
      </div>
    </div>

    <Transition name="bkinv">
      <div v-if="inv" class="scrim" @click.self="inv = false">
        <div class="gui" role="dialog" :aria-label="$t('skinBlocky.inventory')">
          <div class="ghead">
            <h2>{{ $t('skinBlocky.inventory') }}</h2>
            <span class="kbd">{{ editing ? $t('skinBlocky.pinCount', { n: pins.keys.value.length, max: pins.max }) : $t('skinBlocky.keys') }}</span>
            <button type="button" class="gbtn gtxt" :class="{ on: editing }" :aria-pressed="editing" @click="editing = !editing">{{ editing ? $t('skinBlocky.done') : $t('skinBlocky.editBar') }}</button>
            <button type="button" class="gbtn" :aria-label="$t('skinBlocky.search')" @click="inv = false; emit('search')"><Icon name="search" :size="18" /></button>
            <button type="button" class="gbtn" :aria-label="$t('skinBlocky.close')" @click="inv = false">{{ '×' }}</button>
          </div>
          <div v-if="editing" class="ghint">{{ $t('skinBlocky.pinHint', { max: pins.max }) }}</div>
          <div class="ggrid">
            <button v-for="n in nav" :key="n.to" type="button" class="gslot"
              :class="{ on: n.to === path, glint: !!mark(n.to), pinned: editing && pins.isPinned(n.to), dim: editing && pins.full.value && !pins.isPinned(n.to) }"
              :aria-pressed="editing ? pins.isPinned(n.to) : undefined" @click="pick(n.to)">
              <span class="gi"><Icon :name="n.icon" :size="24" /><span v-if="badge(n.to)" class="count">{{ badge(n.to) }}</span></span>
              <span class="gl">{{ n.label }}</span>
              <span v-if="editing && pins.isPinned(n.to)" class="gpin">{{ pins.keys.value.indexOf(n.to) + 1 }}</span>
            </button>
          </div>
          <div class="gfoot">
            <span class="dot" :class="state" /><span>{{ up }} · {{ stateText }}</span>
            <span class="lv">{{ $t('skinBlocky.level', { n: level }) }}</span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.defs { position: absolute; width: 0; height: 0; overflow: hidden; }
.blocky-nav { --slot: min(46px, calc((100vw - 76px) / 9)); font-family: "Courier New", Courier, monospace; font-weight: 700; }
.hud {
  position: fixed; z-index: 60; left: 50%; bottom: calc(6px + env(safe-area-inset-bottom)); transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center; gap: 3px; pointer-events: none;
}
.hud > * { pointer-events: auto; }

.iname {
  position: absolute; bottom: calc(100% + 4px); left: 50%; transform: translateX(-50%); white-space: nowrap; pointer-events: none;
  padding: 2px 8px; font-size: 15px; color: var(--text); text-shadow: 2px 2px 0 rgba(60, 60, 60, 1); background: rgba(0, 0, 0, .35);
}
.bkname-enter-active { transition: opacity .1s; }
.bkname-leave-active { transition: opacity .5s steps(4); }
.bkname-enter-from, .bkname-leave-to { opacity: 0; }
.jobs { position: absolute; bottom: calc(100% + 30px); right: 0; }
.jobs :deep(.jt) { border-radius: 0; border: 2px solid rgba(0, 0, 0, 1); background: rgba(16, 0, 16, .85); color: var(--text); box-shadow: inset 0 0 0 1px rgba(90, 42, 168, 1); }

.stats { display: flex; justify-content: space-between; width: 100%; padding: 0 2px; }
.hearts, .hunger { display: flex; gap: 0; }
.hunger { flex-direction: row; }
.pip { width: calc(var(--slot) * .36); height: calc(var(--slot) * .36); margin-right: -1px; image-rendering: pixelated; filter: drop-shadow(1px 1px 0 rgba(0, 0, 0, .35)); }
.hearts.low .pip { animation: shake .45s steps(2) infinite; }
@keyframes shake { 50% { transform: translateY(-2px); } }

.xp { position: relative; width: calc(100% - 4px); height: 7px; background: rgba(0, 0, 0, .8); border: 1px solid rgba(0, 0, 0, 1); }
.xpfill { position: absolute; inset: 1px; background: linear-gradient(180deg, rgba(150, 255, 90, 1), rgba(70, 190, 30, 1)); transform-origin: left; }
.lvl {
  position: absolute; left: 50%; top: -15px; transform: translateX(-50%); font-size: 14px; line-height: 1; color: rgba(128, 255, 32, 1);
  text-shadow: 1px 0 0 rgba(0, 0, 0, 1), -1px 0 0 rgba(0, 0, 0, 1), 0 1px 0 rgba(0, 0, 0, 1), 0 -1px 0 rgba(0, 0, 0, 1);
}

.barrow { display: flex; align-items: center; gap: 6px; margin-top: 2px; }
.hotbar { display: flex; padding: 3px; background: rgba(20, 20, 20, .72); border: 2px solid rgba(0, 0, 0, 1); box-shadow: inset 0 0 0 2px rgba(110, 110, 110, .9); }
.slot {
  position: relative; display: grid; place-items: center; width: var(--slot); height: var(--slot); flex: none; color: var(--text);
  background: rgba(139, 139, 139, .55); text-decoration: none;
  box-shadow: inset 2px 2px 0 rgba(55, 55, 55, 1), inset -2px -2px 0 rgba(200, 200, 200, .9);
  -webkit-tap-highlight-color: transparent;
}
.slot + .slot { margin-left: 2px; }
.slot:hover { text-decoration: none; background: rgba(170, 170, 170, .65); }
.item { filter: drop-shadow(2px 2px 0 rgba(40, 40, 40, 1)); }
.slot.on { z-index: 1; outline: 4px solid rgba(255, 255, 255, 1); outline-offset: 0; box-shadow: inset 0 0 0 2px rgba(0, 0, 0, 1), 0 0 0 6px rgba(0, 0, 0, .9); background: rgba(160, 160, 160, .7); }
.slot.on .item { transform: translateY(-1px) scale(1.1); }
.empty { pointer-events: none; }
.count {
  position: absolute; right: 2px; bottom: 0; font-size: 13px; line-height: 1; color: var(--text);
  text-shadow: 2px 2px 0 rgba(60, 60, 60, 1);
}
.key { position: absolute; left: 3px; top: 2px; font-size: 9px; line-height: 1; color: rgba(255, 255, 255, .55); }
.glint { overflow: hidden; }
.glint::after {
  content: ''; position: absolute; inset: 0; pointer-events: none; mix-blend-mode: screen;
  background: linear-gradient(115deg, rgba(160, 80, 255, 0) 30%, rgba(200, 120, 255, .85) 45%, rgba(160, 80, 255, 0) 60%);
  animation: glint 1.6s linear infinite;
}
.glint.input::after { background: linear-gradient(115deg, rgba(255, 200, 40, 0) 30%, rgba(255, 210, 60, .9) 45%, rgba(255, 200, 40, 0) 60%); }
@keyframes glint { from { transform: translateX(-100%); } to { transform: translateX(100%); } }

.side {
  position: relative; display: grid; place-items: center; width: calc(var(--slot) + 2px); height: calc(var(--slot) + 2px); padding: 0; cursor: pointer; color: var(--text);
  background: rgba(122, 122, 122, 1); border: 2px solid rgba(0, 0, 0, 1);
  box-shadow: inset 2px 2px 0 rgba(170, 170, 170, 1), inset -2px -3px 0 rgba(74, 74, 74, 1);
}
.side:active { transform: scale(1.06, .85); }
.side svg { width: 70%; height: 70%; image-rendering: pixelated; }
.rowtag { position: absolute; right: -4px; top: -8px; padding: 0 3px; font-size: 10px; color: var(--text); background: rgba(0, 0, 0, .85); }

/* inventory GUI */
.scrim { position: fixed; inset: 0; z-index: 90; display: grid; place-items: center; padding: 16px; background: rgba(0, 0, 0, .55); }
.gui {
  width: min(560px, 100%); max-height: calc(100dvh - 40px); display: flex; flex-direction: column; overflow: hidden;
  color: rgba(55, 55, 55, 1); background: rgba(198, 198, 198, 1); border: 2px solid rgba(0, 0, 0, 1);
  box-shadow: inset 3px 3px 0 rgba(255, 255, 255, 1), inset -3px -3px 0 rgba(85, 85, 85, 1), 6px 6px 0 rgba(0, 0, 0, .4);
}
.ghead { display: flex; align-items: center; gap: 8px; padding: 10px 12px 6px; }
.ghead h2 { margin: 0; font-size: 17px; color: rgba(64, 64, 64, 1); text-shadow: none; }
.kbd { flex: 1; font-size: 11px; color: rgba(110, 110, 110, 1); }
.gbtn {
  display: grid; place-items: center; width: 36px; height: 36px; padding: 0; font: inherit; font-size: 20px; cursor: pointer; color: var(--text);
  background: rgba(122, 122, 122, 1); border: 2px solid rgba(0, 0, 0, 1); text-shadow: 2px 2px 0 rgba(58, 58, 58, 1);
  box-shadow: inset 2px 2px 0 rgba(170, 170, 170, 1), inset -2px -3px 0 rgba(74, 74, 74, 1);
}
.gbtn:active { transform: scale(1.06, .85); }
.ggrid { display: grid; grid-template-columns: repeat(auto-fill, minmax(76px, 1fr)); gap: 4px; padding: 6px 12px 10px; overflow-y: auto; }
.gslot {
  position: relative; display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 8px 4px 6px; min-height: 72px; text-decoration: none;
  color: rgba(55, 55, 55, 1); background: rgba(139, 139, 139, 1);
  box-shadow: inset 2px 2px 0 rgba(55, 55, 55, 1), inset -2px -2px 0 rgba(255, 255, 255, 1);
}
.gslot { font: inherit; border: 0; cursor: pointer; }
.gslot:hover { text-decoration: none; background: rgba(170, 170, 170, 1); }
.gslot.pinned { outline: 3px solid rgba(255, 255, 85, 1); outline-offset: -1px; }
.gslot.dim { opacity: .45; }
.gpin {
  position: absolute; left: 3px; top: 2px; min-width: 16px; padding: 0 2px; font-size: 11px; line-height: 16px; text-align: center;
  color: rgba(40, 40, 40, 1); background: rgba(255, 255, 85, 1); border: 1px solid rgba(0, 0, 0, 1);
}
.gtxt { width: auto; padding: 0 10px; font-size: 13px; }
.gtxt.on { background: rgba(80, 160, 40, 1); }
.ghint { padding: 0 12px 4px; font-size: 11.5px; color: rgba(70, 70, 70, 1); }
.gslot.on { outline: 3px solid rgba(255, 255, 255, 1); outline-offset: -1px; }
.gi { position: relative; display: grid; place-items: center; width: 32px; height: 32px; color: var(--text); filter: drop-shadow(2px 2px 0 rgba(40, 40, 40, 1)); }
.gi .count { right: -8px; bottom: -4px; }
.gl { max-width: 100%; font-size: 11.5px; color: var(--text); text-shadow: 1px 1px 0 rgba(40, 40, 40, 1); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.gfoot { display: flex; align-items: center; gap: 8px; padding: 8px 12px 10px; font-size: 12px; border-top: 2px solid rgba(139, 139, 139, 1); }
.gfoot .lv { margin-left: auto; color: rgba(40, 120, 10, 1); }
.dot { width: 10px; height: 10px; background: var(--ok); border: 2px solid rgba(0, 0, 0, 1); }
.dot.warn { background: var(--warn); } .dot.bad { background: var(--bad); }
.bkinv-enter-active { transition: opacity .12s steps(3); }
.bkinv-enter-active .gui { transition: transform .18s steps(4); }
.bkinv-leave-active { transition: opacity .1s; }
.bkinv-enter-from, .bkinv-leave-to { opacity: 0; }
.bkinv-enter-from .gui { transform: scale(.85); }

@media (max-width: 640px) {
  .find { display: none; }
  .key { display: none; }
  .barrow { gap: 4px; }
  html.kb .hud { display: none; }
}
@media (max-width: 640px) and (pointer: coarse) { .hearts.low .pip { animation: none; } }
@media (prefers-reduced-motion: reduce) {
  .hearts.low .pip, .glint::after { animation: none; }
  .bkinv-enter-active .gui { transition: none; }
}
</style>

<style>
/* room for the HUD on every screen size + the button squash; only while this skin is on */
html.skin-blocky .shell.skinned { --tabbar: calc(96px + env(safe-area-inset-bottom)); }
html.skin-blocky main.wrap { padding-bottom: calc(var(--tabbar) + 44px); }
/* icons as chunky pixel items: square ends, hard corners, heavier strokes, no anti-aliased curves */
html.skin-blocky svg.icon { stroke-width: 2.6; stroke-linecap: square; stroke-linejoin: miter; shape-rendering: crispEdges; }
@keyframes skin-blocky-click { 0% { transform: scale(1.06, .82); } 100% { transform: scale(1, 1); } }
@media (prefers-reduced-motion: reduce) { html.skin-blocky .btn:active { animation: none !important; } }
</style>
