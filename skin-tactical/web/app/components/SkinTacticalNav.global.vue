<script setup lang="ts">
/**
 * Tactical HUD, kept calm: desktop = a numbered loadout column (keys 1–9 jump to a page); phone = a slim top bar
 * + a bottom weapon-slot bar (the four pinned pages + "more"). The more sheet lists every page and edits the pins.
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
const slotNo = (i: number) => (i < 9 ? String(i + 1) : '')

const { pinned, isPinned, toggle, editing, full: pinsFull, max } = useNavPins(() => list.value)
const offTab = computed(() => {
  const here = list.value.find(n => n.to === props.path)
  return here && !isPinned(here.to) ? here : null
})
const moreBadge = computed(() => list.value.filter(n => !isPinned(n.to)).reduce((s, n) => s + b(n.to), 0))
const idx = (to: string) => list.value.findIndex(n => n.to === to)
const sheet = ref(false)
watch(sheet, v => { if (!v) editing.value = false })
function pick(to: string) { if (editing.value) toggle(to); else { sheet.value = false; navigateTo(to) } }
watch(() => props.path, () => (sheet.value = false))

function typing(e: KeyboardEvent) {
  const t = e.target as HTMLElement | null
  return !!t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') { sheet.value = false; return }
  if (e.ctrlKey || e.metaKey || e.altKey || e.shiftKey || e.repeat || typing(e)) return
  if (/^[1-9]$/.test(e.key)) {
    const n = list.value[Number(e.key) - 1]
    if (n) { e.preventDefault(); navigateTo(n.to) }
  }
}
watch(() => props.full, v => document.documentElement.classList.toggle('tac-full', v))
onMounted(() => {
  document.documentElement.classList.toggle('tac-full', props.full)
  window.addEventListener('keydown', onKey)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  document.documentElement.classList.remove('tac-full')
})
</script>

<template>
  <div class="tac-nav" :class="{ full }">
    <!-- desktop: loadout column -->
    <aside class="buy" :aria-label="$t('skinTactical.loadout')">
      <header class="bh">
        <NuxtLink to="/" class="brand">{{ 'bastion' }}</NuxtLink>
        <span class="led" :class="state" :title="stateText" />
        <button type="button" class="sb" :aria-label="$t('skinTactical.search')" @click="emit('search')"><Icon name="search" :size="15" /></button>
      </header>
      <nav class="slots-v">
        <NuxtLink v-for="(n, i) in list" :key="n.to" :to="n.to" class="row" :class="{ on: n.to === path }">
          <span class="no">{{ slotNo(i) }}</span>
          <Icon :name="n.icon" :size="16" class="ic" />
          <span class="l">{{ n.label }}</span>
          <span v-if="b(n.to)" class="badge">{{ b(n.to) }}</span>
          <span v-else-if="m(n.to)" class="cm" :class="m(n.to)" />
        </NuxtLink>
      </nav>
      <footer class="bf"><JobsButton /><span class="st">{{ up }} · {{ stateText }}</span></footer>
    </aside>

    <!-- phone: top bar -->
    <div class="ptop">
      <NuxtLink to="/" class="brand">{{ 'bastion' }}</NuxtLink>
      <span class="led" :class="state" />
      <span class="st">{{ up }}</span>
      <div class="tjobs"><JobsButton /></div>
      <button type="button" class="sb" :aria-label="$t('skinTactical.search')" @click="emit('search')"><Icon name="search" :size="18" /></button>
    </div>

    <!-- phone: weapon slots -->
    <nav class="pbar tac-pbar">
      <NuxtLink v-for="n in pinned" :key="n.to" :to="n.to" class="ws" :class="{ on: n.to === path && !sheet }">
        <span class="no">{{ slotNo(idx(n.to)) }}</span>
        <Icon :name="n.icon" :size="20" />
        <span class="l">{{ n.label }}</span>
        <span v-if="b(n.to)" class="badge">{{ b(n.to) }}</span>
        <span v-else-if="m(n.to)" class="cm" :class="m(n.to)" />
      </NuxtLink>
      <button type="button" class="ws" :class="{ on: !!offTab || sheet }" :aria-expanded="sheet" @click="sheet = !sheet">
        <Icon :name="offTab && !sheet ? offTab.icon : 'grid'" :size="20" />
        <span class="l">{{ offTab && !sheet ? offTab.label : $t('skinTactical.more') }}</span>
        <span v-if="moreBadge" class="badge">{{ moreBadge }}</span>
      </button>
    </nav>

    <Transition name="sh">
      <div v-if="sheet" class="scrim" @click.self="sheet = false">
        <div class="sheet" role="dialog" :aria-label="$t('skinTactical.loadout')">
          <header class="bh">
            <b>{{ editing ? $t('skinTactical.pinCount', { n: pinned.length, max }) : $t('skinTactical.loadout') }}</b>
            <button type="button" class="sb ed" :class="{ on: editing }" @click="editing = !editing">
              <Icon name="pin" :size="14" />{{ editing ? $t('skinTactical.done') : $t('skinTactical.editTabs') }}
            </button>
          </header>
          <div class="grid9">
            <button
              v-for="(n, i) in list" :key="n.to" type="button" class="cell"
              :class="{ on: !editing && n.to === path, pin: editing && isPinned(n.to), dim: editing && pinsFull && !isPinned(n.to) }"
              :aria-pressed="editing ? isPinned(n.to) : undefined" @click="pick(n.to)"
            >
              <span class="no">{{ slotNo(i) }}</span>
              <Icon :name="n.icon" :size="22" />
              <span class="l">{{ n.label }}</span>
              <span v-if="editing && isPinned(n.to)" class="pm"><Icon name="pin" :size="11" /></span>
              <span v-else-if="b(n.to)" class="badge">{{ b(n.to) }}</span>
              <span v-else-if="m(n.to)" class="cm" :class="m(n.to)" />
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.tac-nav { --amb: var(--accent); font-family: "Bahnschrift", "Arial Narrow", "Roboto Condensed", system-ui, sans-serif; text-transform: uppercase; letter-spacing: .04em; }
.badge { min-width: 18px; padding: 0 5px; font-size: 11px; line-height: 17px; text-align: center; font-weight: 700; color: var(--bg); background: var(--bad); }
.cm { width: 8px; height: 8px; background: var(--amb); transform: rotate(45deg); flex: none; }
.cm.busy { animation: tac-blink 1s steps(2) infinite; }
.cm.input { background: var(--warn); }
@keyframes tac-blink { 50% { opacity: .2; } }
.brand { font-weight: 800; font-size: 15px; letter-spacing: .14em; color: var(--text); text-decoration: none; }
.led { width: 8px; height: 8px; flex: none; background: var(--ok); }
.led.warn { background: var(--warn); } .led.bad { background: var(--bad); }
.st { font-size: 11px; color: var(--faint); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sb { margin-left: auto; display: inline-flex; align-items: center; justify-content: center; gap: 5px; min-width: 32px; height: 32px; padding: 0 8px; border: 1px solid var(--line-2); background: transparent; color: var(--text); font: inherit; font-size: 12px; cursor: pointer; }
.sb:hover, .sb:focus-visible, .sb.on { border-color: var(--amb); color: var(--amb); outline: none; }

/* desktop loadout column */
.buy { position: fixed; z-index: 60; left: 0; top: 0; bottom: 0; width: 210px; display: flex; flex-direction: column; background: var(--panel); border-right: 1px solid var(--line-2); }
.bh { display: flex; align-items: center; gap: 8px; padding: 10px 8px 10px 12px; border-bottom: 1px solid var(--line); font-size: 13px; color: var(--amb); }
.slots-v { flex: 1; overflow-y: auto; padding: 6px 4px; display: flex; flex-direction: column; gap: 1px; }
.row { display: flex; align-items: center; gap: 9px; min-height: 34px; padding: 3px 8px 3px 6px; color: var(--muted); font-size: 13.5px; text-decoration: none; border-left: 2px solid transparent; }
.row:hover, .row:focus-visible { color: var(--text); background: color-mix(in srgb, var(--amb) 8%, transparent); text-decoration: none; outline: none; }
.row.on { color: var(--text); border-left-color: var(--amb); background: color-mix(in srgb, var(--amb) 14%, transparent); }
.row .no { width: 14px; flex: none; font-size: 11px; color: var(--faint); text-align: right; }
.row.on .no, .row.on .ic { color: var(--amb); }
.row .ic { flex: none; }
.row .l { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bf { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-top: 1px solid var(--line); }
.bf .st { margin-left: auto; text-transform: none; }

/* phone */
.ptop, .pbar, .scrim { display: none; }
@media (max-width: 640px) {
  .buy { display: none; }
  .ptop { display: flex; align-items: center; gap: 8px; position: fixed; z-index: 60; left: 0; right: 0; top: 0; height: calc(44px + env(safe-area-inset-top, 0px)); padding: env(safe-area-inset-top, 0px) 6px 0 12px; background: var(--bg); border-bottom: 1px solid var(--line-2); }
  .ptop .st { text-transform: none; }
  .tjobs { margin-left: auto; display: flex; }
  .tjobs :deep(.jt) { min-height: 32px; padding: 3px 8px; border-radius: 0; gap: 0; }
  .tjobs :deep(.jt .l) { display: none; }
  .ptop .sb { margin-left: 0; width: 36px; }
  .full .ptop { display: none; }
  .pbar { display: flex; gap: 3px; position: fixed; left: 0; right: 0; bottom: 0; z-index: 60; height: calc(54px + env(safe-area-inset-bottom)); padding: 3px 3px calc(3px + env(safe-area-inset-bottom)); background: var(--bg); border-top: 1px solid var(--line-2); }
  .ws { position: relative; flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; padding: 0 2px; color: var(--muted); background: transparent; border: 0; border-top: 2px solid transparent; font: inherit; text-decoration: none; cursor: pointer; }
  .ws.on { color: var(--text); border-top-color: var(--amb); background: color-mix(in srgb, var(--amb) 10%, transparent); }
  .ws.on :deep(svg) { color: var(--amb); }
  .ws .no { position: absolute; top: 2px; left: 4px; font-size: 9.5px; color: var(--faint); }
  .ws .l { max-width: 100%; font-size: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .ws .badge, .ws .cm { position: absolute; top: 3px; right: 4px; }
  .scrim { display: flex; align-items: flex-end; position: fixed; inset: 0; z-index: 65; background: rgba(0, 0, 0, .6); }
  .sheet { width: 100%; max-height: 78dvh; display: flex; flex-direction: column; padding-bottom: calc(var(--tabbar, 56px) + 4px); background: var(--panel); border-top: 2px solid var(--amb); }
  .sheet .bh b { font-size: 13px; }
  .grid9 { overflow-y: auto; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 4px; padding: 6px; }
  .cell { position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; min-height: 66px; padding: 6px 4px; color: var(--muted); background: transparent; border: 1px solid var(--line); font: inherit; text-transform: uppercase; cursor: pointer; }
  .cell.on, .cell.pin { color: var(--text); border-color: var(--amb); background: color-mix(in srgb, var(--amb) 12%, transparent); }
  .cell.dim { opacity: .4; }
  .cell .no { position: absolute; top: 3px; left: 5px; font-size: 10.5px; color: var(--faint); }
  .cell .l { max-width: 100%; font-size: 11.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .cell .badge, .cell .cm, .cell .pm { position: absolute; top: 4px; right: 4px; }
  .pm { display: grid; place-items: center; width: 18px; height: 18px; color: var(--bg); background: var(--amb); }
  .sh-enter-active, .sh-leave-active { transition: opacity .15s; }
  .sh-enter-active .sheet, .sh-leave-active .sheet { transition: transform .15s ease-out; }
  .sh-enter-from, .sh-leave-to { opacity: 0; }
  .sh-enter-from .sheet, .sh-leave-to .sheet { transform: translateY(40px); }
}
@media (prefers-reduced-motion: reduce) {
  .sh-enter-active, .sh-leave-active, .sh-enter-active .sheet, .sh-leave-active .sheet { transition: none; }
  .cm.busy { animation: none; }
}
</style>

<style>
/* only while this skin is on: room for the column / phone bars, square crisp icons, mono emoji, page transition */
html.skin-tactical body { background: transparent; font-family: "Bahnschrift", "Arial Narrow", "Roboto Condensed", system-ui, 'Bastion Emoji', sans-serif; }
html.skin-tactical svg.icon { stroke-width: 2; stroke-linecap: square; stroke-linejoin: miter; shape-rendering: geometricPrecision; }
@media (min-width: 641px) {
  html.skin-tactical .shell.skinned { padding-left: 210px; }
  html.skin-tactical main.wrap { padding-top: 24px; padding-bottom: 48px; }
}
@media (max-width: 640px) {
  html.skin-tactical { --ptabs-top: calc(45px + env(safe-area-inset-top, 0px)); }
  html.skin-tactical .shell.skinned { --tabbar: calc(55px + env(safe-area-inset-bottom)); }
  html.skin-tactical main.wrap { padding-top: calc(56px + env(safe-area-inset-top, 0px)); padding-bottom: calc(var(--tabbar) + 24px); }
  html.skin-tactical.tac-full main.wrap { padding-top: 12px; }
  html.skin-tactical.kb .tac-pbar { display: none; }
}
html.skin-tactical .sec { text-transform: uppercase; letter-spacing: .06em; }
.skin-tactical-leave-active { transition: opacity .1s linear; }
.skin-tactical-leave-to { opacity: 0; }
.skin-tactical-enter-active { transition: opacity .16s ease-out; }
.skin-tactical-enter-from { opacity: 0; }
</style>
