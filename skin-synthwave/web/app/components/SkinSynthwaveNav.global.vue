<script setup lang="ts">
/**
 * Synthwave navigation. Desktop: a neon sign bar along the top, every page a neon tube that flickers on when it
 * becomes the current page and hums dimly otherwise. Phone: a neon bar at the bottom (4 pinned pages + "more" =
 * a sheet with every page). Props are the layout's own.
 */
type Item = { to: string, icon: string, label: string }
const props = withDefaults(defineProps<{
  nav?: Item[], path?: string
  badge?: (to: string) => number, mark?: (to: string) => string
  state?: string, stateText?: string, up?: string, full?: boolean
}>(), { nav: () => [], path: '', state: 'ok', stateText: '', up: '', full: false })
const emit = defineEmits<{ search: [] }>()

const list = computed(() => props.nav ?? [])
const b = (to: string) => props.badge?.(to) ?? 0
const m = (to: string) => props.mark?.(to) ?? ''

const { pinned, isPinned, toggle, editing, full: pinsFull, max, keys } = useNavPins(() => list.value)
const offTab = computed(() => {
  const here = list.value.find(n => n.to === props.path)
  return here && !pinned.value.some(p => p.to === here.to) ? here : null
})
const moreBadge = computed(() => list.value.filter(n => !pinned.value.some(p => p.to === n.to)).reduce((s, n) => s + b(n.to), 0))
const moreMark = computed(() => {
  const ms = list.value.filter(n => !pinned.value.some(p => p.to === n.to)).map(n => m(n.to))
  return ms.includes('input') ? 'input' : ms.includes('busy') ? 'busy' : ''
})

const sheet = ref(false)
function go(to: string) { if (editing.value) return toggle(to); sheet.value = false; navigateTo(to) }
watch(() => props.path, () => (sheet.value = false))
watch(sheet, v => { if (!v) editing.value = false })

// the sign scrolls sideways when there are more tubes than room; a mouse wheel scrolls it too
const tubes = ref<HTMLElement | null>(null)
function wheel(e: WheelEvent) {
  const el = tubes.value
  if (!el || el.scrollWidth <= el.clientWidth || Math.abs(e.deltaX) > Math.abs(e.deltaY)) return
  e.preventDefault()
  el.scrollLeft += e.deltaY
}
function reveal() {
  nextTick(() => tubes.value?.querySelector('.tube.on')?.scrollIntoView({ block: 'nearest', inline: 'nearest' }))
}
watch(() => props.path, reveal)
const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') sheet.value = false }
onMounted(() => { window.addEventListener('keydown', onKey); reveal() })
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="sw-nav">
    <!-- desktop: neon sign bar -->
    <header class="sign">
      <NuxtLink to="/" class="brand">{{ 'bastion' }}</NuxtLink>
      <nav ref="tubes" class="tubes" @wheel="wheel">
        <NuxtLink v-for="(n, i) in list" :key="n.to" :to="n.to" class="tube" :class="[{ on: n.to === path }, 'h' + (i % 3)]">
          <span class="l">{{ n.label }}</span>
          <span v-if="b(n.to)" class="badge">{{ b(n.to) }}</span>
          <span v-else-if="m(n.to)" class="cm" :class="m(n.to)" />
        </NuxtLink>
      </nav>
      <div class="right">
        <JobsButton />
        <button type="button" class="ib" :aria-label="$t('skinSynthwave.search')" @click="emit('search')"><Icon name="search" :size="17" /></button>
        <span class="led" :class="state" :title="stateText" />
        <span class="up">{{ up }}</span>
      </div>
    </header>

    <!-- phone: bottom neon bar -->
    <nav class="pbar" :data-skin-bar="sheet ? undefined : ''">
      <NuxtLink v-for="n in pinned" :key="n.to" :to="n.to" class="pt" :class="{ on: n.to === path && !sheet }">
        <Icon :name="n.icon" :size="20" />
        <span class="l">{{ n.label }}</span>
        <span v-if="b(n.to)" class="badge">{{ b(n.to) }}</span>
        <span v-else-if="m(n.to)" class="cm" :class="m(n.to)" />
      </NuxtLink>
      <button type="button" class="pt" :class="{ on: !!offTab || sheet }" :aria-expanded="sheet" @click="sheet = !sheet">
        <Icon :name="offTab && !sheet ? offTab.icon : 'grid'" :size="20" />
        <span class="l">{{ offTab && !sheet ? offTab.label : $t('skinSynthwave.more') }}</span>
        <span v-if="moreBadge" class="badge">{{ moreBadge }}</span>
        <span v-else-if="moreMark" class="cm" :class="moreMark" />
      </button>
    </nav>

    <Transition name="swsh">
      <div v-if="sheet" class="scrim" @click.self="sheet = false">
        <div class="sheet" role="dialog" :aria-label="$t('skinSynthwave.pages')">
          <div class="shead">
            <span class="led" :class="state" /><span class="up">{{ up }} · {{ stateText }}</span>
            <JobsButton />
            <button type="button" class="ib" :aria-label="$t('skinSynthwave.search')" @click="sheet = false; emit('search')"><Icon name="search" :size="17" /></button>
            <button type="button" class="ib edit" :class="{ on: editing }" :aria-pressed="editing" @click="editing = !editing">{{ editing ? $t('skinSynthwave.done') : $t('skinSynthwave.editTabs') }}</button>
            <button type="button" class="ib" :aria-label="$t('skinSynthwave.close')" @click="sheet = false"><svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none" /></svg></button>
          </div>
          <div v-if="editing" class="hint">{{ $t('skinSynthwave.pinHint', { n: keys.length, max }) }}</div>
          <div class="plist">
            <button v-for="(n, i) in list" :key="n.to" type="button" class="pi" :class="[{ on: n.to === path && !editing, pinned: editing && isPinned(n.to), dim: editing && pinsFull && !isPinned(n.to) }, 'h' + (i % 3)]" @click="go(n.to)">
              <Icon :name="editing && isPinned(n.to) ? 'pin' : n.icon" :size="20" />
              <span class="l">{{ n.label }}</span>
              <span v-if="b(n.to)" class="badge">{{ b(n.to) }}</span>
              <span v-else-if="m(n.to)" class="cm" :class="m(n.to)" />
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.sw-nav { --pink: var(--accent); --cyan: rgb(52 230 255); --sun: rgb(255 204 77); }
.h0 { --glow: var(--pink); } .h1 { --glow: var(--cyan); } .h2 { --glow: var(--sun); }
.badge { min-width: 18px; padding: 0 5px; border-radius: 9px; font: 700 11px/17px system-ui, sans-serif; text-align: center; color: var(--bg); background: var(--bad); box-shadow: 0 0 8px var(--bad); }
.cm { width: 8px; height: 8px; border-radius: 50%; background: var(--cyan); box-shadow: 0 0 8px var(--cyan); flex: none; }
.cm.busy { animation: sw-pulse 1.2s ease-in-out infinite; }
.cm.input { background: var(--warn); box-shadow: 0 0 8px var(--warn); }
@keyframes sw-pulse { 50% { opacity: .3; } }
.led { width: 9px; height: 9px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 8px var(--ok); flex: none; }
.led.warn { background: var(--warn); box-shadow: 0 0 8px var(--warn); } .led.bad { background: var(--bad); box-shadow: 0 0 8px var(--bad); }
.ib { display: grid; place-items: center; min-width: 34px; height: 34px; border-radius: 8px; border: 1px solid color-mix(in srgb, var(--cyan) 50%, transparent); background: rgba(10, 4, 24, .6); color: var(--cyan); font: inherit; cursor: pointer; }
.ib:hover, .ib:focus-visible { box-shadow: 0 0 10px color-mix(in srgb, var(--cyan) 60%, transparent); outline: none; }
.up { font-size: 12px; color: var(--muted); white-space: nowrap; }

/* desktop sign */
.sign { position: fixed; top: 0; left: 0; right: 0; z-index: 60; height: 60px; display: flex; align-items: center; gap: 14px; padding: 0 16px; background: linear-gradient(180deg, rgba(8, 3, 20, .94), rgba(18, 6, 36, .86)); border-bottom: 1px solid color-mix(in srgb, var(--pink) 60%, transparent); box-shadow: 0 0 18px color-mix(in srgb, var(--pink) 35%, transparent); }
.brand { font: italic 700 24px/1 "Brush Script MT", "Segoe Script", "Lucida Handwriting", cursive; color: var(--text); text-shadow: 0 0 4px var(--pink), 0 0 12px var(--pink), 0 0 24px var(--pink); padding-right: 6px; text-decoration: none; flex: none; }
.brand:hover { text-decoration: none; }
.tubes { flex: 1; min-width: 0; display: flex; align-items: center; gap: 4px; overflow-x: auto; scrollbar-width: none; padding: 4px 2px; }
.tubes::-webkit-scrollbar { display: none; }
.tube { position: relative; display: flex; align-items: center; gap: 6px; flex: none; min-height: 36px; padding: 4px 12px; border-radius: 18px; font: 600 15px/1 "Arial Rounded MT Bold", "Varela Round", "Trebuchet MS", system-ui, sans-serif; letter-spacing: .03em; text-decoration: none; white-space: nowrap; color: color-mix(in srgb, var(--glow) 45%, var(--faint)); text-shadow: 0 0 2px color-mix(in srgb, var(--glow) 30%, transparent); border: 1px solid transparent; transition: color .2s; }
.tube:hover, .tube:focus-visible { color: color-mix(in srgb, var(--glow) 75%, var(--text)); text-decoration: none; outline: none; }
.tube.on { color: var(--text); border-color: color-mix(in srgb, var(--glow) 70%, transparent); text-shadow: 0 0 3px var(--glow), 0 0 10px var(--glow), 0 0 22px var(--glow); box-shadow: 0 0 10px color-mix(in srgb, var(--glow) 45%, transparent), inset 0 0 10px color-mix(in srgb, var(--glow) 30%, transparent); animation: sw-flicker .7s linear 1; }
@keyframes sw-flicker { 0%, 12%, 22%, 36% { opacity: .25; } 8%, 18%, 30%, 44%, 100% { opacity: 1; } }
.right { display: flex; align-items: center; gap: 10px; flex: none; }

/* phone */
.pbar, .scrim { display: none; }
@media (max-width: 640px) {
  .sign { display: none; }
  .pbar { position: fixed; left: 0; right: 0; bottom: 0; z-index: 60; display: flex; gap: 2px; height: calc(60px + env(safe-area-inset-bottom)); padding: 4px 4px env(safe-area-inset-bottom); background: linear-gradient(180deg, rgba(18, 6, 36, .9), rgba(8, 3, 20, .97)); border-top: 1px solid color-mix(in srgb, var(--pink) 70%, transparent); box-shadow: 0 0 18px color-mix(in srgb, var(--pink) 40%, transparent); }
  .pt { position: relative; flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; border: 0; border-radius: 10px; background: none; color: var(--faint); font: 600 10.5px/1.1 "Trebuchet MS", system-ui, sans-serif; text-decoration: none; cursor: pointer; }
  .pt .l { max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .pt.on { color: var(--text); text-shadow: 0 0 6px var(--pink), 0 0 14px var(--pink); animation: sw-flicker .6s linear 1; }
  .pt.on :deep(svg) { color: var(--pink); filter: drop-shadow(0 0 4px var(--pink)); }
  .pt .badge, .pt .cm { position: absolute; top: 2px; right: 10%; }
  .scrim { display: flex; align-items: flex-end; position: fixed; inset: 0; z-index: 59; background: rgba(6, 2, 16, .6); }
  .sheet { width: 100%; max-height: 80dvh; display: flex; flex-direction: column; padding-bottom: calc(64px + env(safe-area-inset-bottom)); background: rgba(14, 6, 30, .97); border-top: 1px solid var(--cyan); border-radius: 16px 16px 0 0; box-shadow: 0 -4px 24px color-mix(in srgb, var(--cyan) 30%, transparent); }
  .shead { display: flex; align-items: center; gap: 8px; padding: 10px 12px; border-bottom: 1px solid var(--line); }
  .shead .up { flex: 1; overflow: hidden; text-overflow: ellipsis; }
  .plist { overflow-y: auto; padding: 8px; display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
  .pi { position: relative; display: flex; align-items: center; gap: 10px; min-height: 46px; padding: 6px 12px; border-radius: 23px; border: 1px solid color-mix(in srgb, var(--glow) 35%, transparent); background: rgba(0, 0, 0, .25); color: color-mix(in srgb, var(--glow) 55%, var(--muted)); font: 600 14px/1.1 "Trebuchet MS", system-ui, sans-serif; text-align: left; cursor: pointer; }
  .pi .l { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .pi.pinned { color: var(--text); border-color: var(--glow); box-shadow: inset 0 0 10px color-mix(in srgb, var(--glow) 40%, transparent); }
  .pi.dim { opacity: .4; }
  .edit { padding: 0 10px; font: 600 12px/1 "Trebuchet MS", system-ui, sans-serif; text-transform: uppercase; letter-spacing: .06em; }
  .edit.on { color: var(--text); border-color: var(--pink); box-shadow: 0 0 10px color-mix(in srgb, var(--pink) 60%, transparent); }
  .hint { padding: 8px 14px 0; font-size: 12px; color: var(--cyan); }
  .pi.on { color: var(--text); border-color: var(--glow); text-shadow: 0 0 8px var(--glow); box-shadow: 0 0 10px color-mix(in srgb, var(--glow) 40%, transparent); }
  .swsh-enter-active, .swsh-leave-active { transition: opacity .18s; }
  .swsh-enter-active .sheet, .swsh-leave-active .sheet { transition: transform .18s ease-out; }
  .swsh-enter-from, .swsh-leave-to { opacity: 0; }
  .swsh-enter-from .sheet, .swsh-leave-to .sheet { transform: translateY(60px); }
}
@media (max-width: 900px) and (min-width: 641px) { .up { display: none; } }
@media (prefers-reduced-motion: reduce) {
  .tube.on, .pt.on, .cm.busy { animation: none; }
  .swsh-enter-active, .swsh-leave-active, .swsh-enter-active .sheet, .swsh-leave-active .sheet { transition: none; }
}
</style>

<style>
/* only while this skin is on: room for the sign (desktop) / neon bar (phone), shared colours, the VHS page change */
html.skin-synthwave body { background: transparent; }
html.skin-synthwave svg.icon { stroke-width: 2; }
@media (min-width: 641px) and (pointer: fine) { html.skin-synthwave svg.icon { filter: drop-shadow(0 0 2px currentColor) drop-shadow(0 0 5px color-mix(in srgb, currentColor 55%, transparent)); } }
@media (min-width: 641px) { html.skin-synthwave .shell.skinned { padding-top: 62px; } }
@media (max-width: 640px) {
  html.skin-synthwave .shell.skinned { --tabbar: calc(62px + env(safe-area-inset-bottom)); }
  html.skin-synthwave main.wrap { padding-bottom: calc(84px + env(safe-area-inset-bottom)); }
}
html.skin-synthwave .skin-synthwave-enter-active { transition: opacity .18s ease-out; }
html.skin-synthwave .skin-synthwave-leave-active { transition: opacity .1s linear; }
html.skin-synthwave .skin-synthwave-enter-from, html.skin-synthwave .skin-synthwave-leave-to { opacity: 0; }
/* the VHS glitch (clip-path + filter) is desktop only; a phone just fades */
@media (min-width: 641px) and (pointer: fine) {
  html.skin-synthwave .skin-synthwave-enter-active { transition: none; animation: sw-glitch .3s linear; }
  html.skin-synthwave .skin-synthwave-leave-active { transition: none; animation: sw-glitch-out .12s linear; }
}
@keyframes sw-glitch {
  0% { opacity: 0; transform: translateX(-10px); clip-path: inset(42% 0 36% 0); filter: drop-shadow(5px 0 rgba(255, 0, 90, .9)) drop-shadow(-5px 0 rgba(0, 240, 255, .9)); }
  18% { opacity: 1; transform: translateX(8px) skewX(-3deg); clip-path: inset(8% 0 62% 0); }
  36% { transform: translateX(-5px); clip-path: inset(66% 0 6% 0); filter: drop-shadow(-4px 0 rgba(255, 0, 90, .8)) drop-shadow(4px 0 rgba(0, 240, 255, .8)); }
  54% { transform: translateX(3px); clip-path: inset(0 0 30% 0); }
  72% { transform: translateX(-1px); clip-path: inset(0); filter: drop-shadow(2px 0 rgba(255, 0, 90, .6)) drop-shadow(-2px 0 rgba(0, 240, 255, .6)); }
  100% { opacity: 1; transform: none; clip-path: inset(0); filter: none; }
}
@keyframes sw-glitch-out { to { opacity: 0; transform: translateX(6px) skewX(4deg); } }
@media (prefers-reduced-motion: reduce) { html.skin-synthwave .skin-synthwave-enter-active, html.skin-synthwave .skin-synthwave-leave-active { animation: none; transition: none; } }
</style>
