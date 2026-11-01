<script setup lang="ts">
/**
 * Grimoire navigation: a leather-bound book.
 * Desktop: a leather sidebar with a gold rule; pages are entries in a table of contents, the open one carries a
 * crimson ribbon bookmark. Phone: a leather bar with the four pinned pages + "more", which opens the contents as a
 * parchment sheet (edit tabs there picks the four, useNavPins).
 */
const props = withDefaults(defineProps<{
  nav?: { to: string, icon: string, label: string }[], path?: string
  badge?: (to: string) => number, mark?: (to: string) => string
  state?: string, stateText?: string, up?: string, full?: boolean
}>(), { nav: () => [], path: '/', badge: () => 0, mark: () => '', state: 'ok', stateText: '', up: '', full: false })
const emit = defineEmits<{ search: [] }>()

const { pinned, isPinned, toggle, editing, full: pinsFull, keys, max } = useNavPins(() => props.nav)
const here = computed(() => props.nav.find(n => n.to === props.path))
const offTab = computed(() => (here.value && !isPinned(here.value.to) ? here.value : null))
const restBadge = computed(() => props.nav.filter(n => !isPinned(n.to)).reduce((s, n) => s + props.badge(n.to), 0))
const restMark = computed(() => props.nav.filter(n => !isPinned(n.to)).map(n => props.mark(n.to)).find(Boolean) ?? '')

const sheet = ref(false)
function close() { sheet.value = false; editing.value = false }
function openSheet() { if (sheet.value) close(); else { editing.value = false; sheet.value = true } }
function pick(to: string) { if (editing.value) toggle(to); else { close(); navigateTo(to) } }
function search() { close(); emit('search') }
watch(() => props.path, close)
const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') close() }
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="gm-nav" :class="{ full }">
    <!-- desktop: the leather sidebar -->
    <aside class="side">
      <NuxtLink to="/" class="brand">{{ 'bastion' }}</NuxtLink>
      <button type="button" class="find" @click="search"><Icon name="search" :size="15" /><span class="l">{{ $t('skinGrimoire.search') }}</span></button>
      <nav class="toc">
        <NuxtLink v-for="n in nav" :key="n.to" :to="n.to" class="page" :class="{ on: n.to === path }">
          <Icon :name="n.icon" :size="16" />
          <span class="l">{{ n.label }}</span>
          <span v-if="badge(n.to)" class="badge">{{ badge(n.to) }}</span>
          <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
        </NuxtLink>
      </nav>
      <div class="foot">
        <JobsButton />
        <span class="st" :title="stateText"><span class="dot" :class="state" /><span class="l">{{ up }} · {{ stateText }}</span></span>
      </div>
    </aside>

    <!-- phone: jobs float top right (only when there are any), the bar sits at the bottom -->
    <div class="phone-jobs"><JobsButton /></div>
    <nav class="bar">
      <NuxtLink v-for="n in pinned" :key="n.to" :to="n.to" class="tab" :class="{ on: n.to === path && !sheet }">
        <span class="ti"><Icon :name="n.icon" :size="21" /><span v-if="badge(n.to)" class="badge">{{ badge(n.to) }}</span><span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" /></span>
        <span class="l">{{ n.label }}</span>
      </NuxtLink>
      <button type="button" class="tab" :class="{ on: offTab || sheet }" :aria-expanded="sheet" @click="openSheet">
        <span class="ti"><Icon :name="offTab && !sheet ? offTab.icon : 'book'" :size="21" /><span v-if="restBadge" class="badge">{{ restBadge }}</span><span v-else-if="restMark" class="cm" :class="restMark" /></span>
        <span class="l">{{ offTab && !sheet ? offTab.label : $t('skinGrimoire.more') }}</span>
      </button>
    </nav>

    <Transition name="gm-sheet">
      <div v-if="sheet" class="scrim" @click.self="close">
        <div class="sheet" role="dialog" :aria-label="$t('skinGrimoire.title')">
          <div class="sh">
            <span class="dot" :class="state" />
            <span class="st">{{ up }} · {{ stateText }}</span>
            <button type="button" class="sb" :aria-label="$t('skinGrimoire.search')" @click="search"><Icon name="search" :size="16" /></button>
            <button type="button" class="sb ed" :class="{ on: editing }" @click="editing = !editing">{{ editing ? $t('skinGrimoire.done') : $t('skinGrimoire.editTabs') }}</button>
          </div>
          <p v-if="editing" class="hint">{{ $t('skinGrimoire.pinHint', { n: keys.length, max }) }}</p>
          <div class="entries">
            <button v-for="n in nav" :key="n.to" type="button" class="entry"
              :class="{ on: n.to === path && !editing, pinned: editing && isPinned(n.to), dim: editing && !isPinned(n.to) && pinsFull }"
              @click="pick(n.to)">
              <Icon :name="n.icon" :size="18" />
              <span class="l">{{ n.label }}</span>
              <span v-if="editing && isPinned(n.to)" class="pm"><Icon name="pin" :size="13" /></span>
              <span v-else-if="badge(n.to)" class="badge">{{ badge(n.to) }}</span>
              <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.gm-nav { font-family: Georgia, "Palatino Linotype", Palatino, serif, 'Bastion Emoji'; }
.badge { min-width: 18px; padding: 0 5px; border-radius: 2px; font: 700 10.5px/17px system-ui, sans-serif; text-align: center; color: var(--text); background: var(--bad); }
.cm { width: 8px; height: 8px; border-radius: 50%; background: var(--warn); }
.cm.busy { animation: gm-pulse 1.4s ease-in-out infinite; }
.cm.input { background: var(--accent); }
@keyframes gm-pulse { 50% { opacity: .3; } }
.l { min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* ---- desktop: leather sidebar ---- */
.side {
  position: fixed; z-index: 60; top: 0; bottom: 0; left: 0; width: 232px; display: flex; flex-direction: column; gap: 10px; padding: 22px 14px 14px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--accent) 12%, var(--bg)), var(--bg));
  border-right: 1px solid color-mix(in srgb, var(--warn) 40%, transparent);
  box-shadow: inset -5px 0 0 -4px color-mix(in srgb, var(--warn) 18%, transparent);
}
.brand { padding: 0 8px 12px; font-size: 15px; letter-spacing: .38em; text-transform: uppercase; color: var(--warn); text-decoration: none; border-bottom: 1px solid color-mix(in srgb, var(--warn) 30%, transparent); }
.brand:hover { text-decoration: none; }
.find { display: flex; align-items: center; gap: 8px; min-height: 34px; padding: 6px 10px; font: inherit; font-size: 13px; color: var(--muted); background: none; border: 1px solid color-mix(in srgb, var(--warn) 25%, transparent); border-radius: 3px; cursor: pointer; }
.find:hover { color: var(--text); border-color: color-mix(in srgb, var(--warn) 55%, transparent); }
.toc { flex: 1; min-height: 0; overflow-y: auto; display: flex; flex-direction: column; gap: 1px; scrollbar-width: thin; }
.page { position: relative; display: flex; align-items: center; gap: 10px; min-height: 34px; padding: 4px 26px 4px 8px; flex: none; color: var(--muted); font-size: 14px; text-decoration: none; border-radius: 2px; }
.page .l { flex: 1; }
.page:hover { text-decoration: none; color: var(--text); }
.page.on { color: var(--warn); background: color-mix(in srgb, var(--warn) 7%, transparent); }
/* the ribbon bookmark on the open page */
.page.on::after { content: ''; position: absolute; right: 6px; top: -3px; width: 9px; height: calc(100% + 9px); background: var(--accent); clip-path: polygon(0 0, 100% 0, 100% 100%, 50% 78%, 0 100%); }
.foot { display: flex; flex-direction: column; gap: 8px; padding-top: 10px; border-top: 1px solid color-mix(in srgb, var(--warn) 20%, transparent); }
.st { display: flex; align-items: center; gap: 8px; min-width: 0; font-size: 12px; color: var(--faint); }

.bar, .phone-jobs { display: none; }

@media (max-width: 900px) and (min-width: 641px) {
  .side { width: 72px; align-items: center; padding: 18px 8px 12px; }
  .side .l, .brand { display: none; }
  .find { justify-content: center; padding: 8px; }
  .page { justify-content: center; padding: 4px; }
  .page .badge, .page .cm { position: absolute; top: 0; right: 0; }
  .page.on::after { right: -4px; width: 6px; }
  .foot { align-items: center; }
}

/* ---- phone ---- */
@media (max-width: 640px) {
  .side { display: none; }
  .phone-jobs { display: block; position: fixed; z-index: 60; top: calc(env(safe-area-inset-top) + 8px); right: 8px; }
  .phone-jobs:empty { display: none; }
  .bar {
    position: fixed; z-index: 70; left: 0; right: 0; bottom: 0; display: flex;
    height: calc(56px + env(safe-area-inset-bottom)); padding: 0 4px env(safe-area-inset-bottom);
    background: color-mix(in srgb, var(--accent) 8%, var(--bg));
    border-top: 1px solid color-mix(in srgb, var(--warn) 45%, transparent);
  }
  .tab { position: relative; flex: 1; display: flex; flex-direction: column; align-items: center; gap: 3px; min-width: 0; height: 56px; padding: 8px 2px 0; font: inherit; font-size: 11px; color: var(--muted); background: none; border: 0; text-decoration: none; cursor: pointer; -webkit-tap-highlight-color: transparent; }
  .tab:hover { text-decoration: none; }
  .tab.on { color: var(--warn); }
  .tab.on::before { content: ''; position: absolute; top: -1px; left: 50%; width: 10px; height: 11px; margin-left: -5px; background: var(--accent); clip-path: polygon(0 0, 100% 0, 100% 100%, 50% 65%, 0 100%); }
  .ti { position: relative; display: grid; place-items: center; }
  .ti .badge { position: absolute; top: -6px; left: 14px; }
  .ti .cm { position: absolute; top: -2px; left: 18px; }
  .tab .l { max-width: 100%; }
}

/* ---- the contents sheet ---- */
.scrim { position: fixed; inset: 0; z-index: 65; display: flex; align-items: flex-end; padding: 10px 10px calc(66px + env(safe-area-inset-bottom)); background: rgba(0, 0, 0, .6); }
.sheet {
  width: 100%; max-height: 100%; display: flex; flex-direction: column; gap: 8px; padding: 12px; overflow: hidden;
  color: var(--text); background: var(--panel); border: 1px solid color-mix(in srgb, var(--warn) 40%, transparent); border-radius: 3px;
  outline: 1px solid color-mix(in srgb, var(--warn) 15%, transparent); outline-offset: -5px;
}
.sh { display: flex; align-items: center; gap: 8px; padding: 0 2px 8px; border-bottom: 1px solid color-mix(in srgb, var(--warn) 25%, transparent); }
.sh .st { flex: 1; }
.sb { display: inline-flex; align-items: center; justify-content: center; min-width: 36px; height: 34px; padding: 0 10px; font: inherit; font-size: 13px; color: var(--muted); background: none; border: 1px solid color-mix(in srgb, var(--warn) 30%, transparent); border-radius: 3px; cursor: pointer; }
.sb.on { color: var(--bg); background: var(--warn); border-color: var(--warn); }
.hint { margin: 0; font-size: 12.5px; font-style: italic; color: var(--muted); }
.entries { min-height: 0; overflow-y: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.entry {
  position: relative; display: flex; align-items: center; gap: 9px; min-height: 44px; min-width: 0; padding: 6px 10px;
  font: inherit; font-size: 14px; color: var(--text); text-align: left; cursor: pointer;
  background: none; border: 1px solid color-mix(in srgb, var(--warn) 20%, transparent); border-radius: 3px;
}
.entry .l { flex: 1; }
.entry.on { color: var(--warn); border-color: color-mix(in srgb, var(--warn) 60%, transparent); }
.entry.pinned { border-color: var(--warn); background: color-mix(in srgb, var(--warn) 10%, transparent); }
.entry.dim { opacity: .45; }
.pm { display: grid; place-items: center; color: var(--warn); }
.gm-sheet-enter-active, .gm-sheet-leave-active { transition: opacity .2s; }
.gm-sheet-enter-active .sheet, .gm-sheet-leave-active .sheet { transition: transform .2s ease-out; }
.gm-sheet-enter-from, .gm-sheet-leave-to { opacity: 0; }
.gm-sheet-enter-from .sheet, .gm-sheet-leave-to .sheet { transform: translateY(16px); }
@media (min-width: 641px) { .scrim { align-items: center; justify-content: center; padding: 20px; } .sheet { width: min(460px, 100%); } }
@media (max-width: 340px) { .entries { grid-template-columns: 1fr; } }
@media (prefers-reduced-motion: reduce) { .cm.busy { animation: none; } }
</style>

<style>
/* the skin's global part: serif ink, gold rules, crimson accents; room for the sidebar / the bar */
html.skin-grimoire body { font-family: Georgia, "Palatino Linotype", Palatino, serif, 'Bastion Emoji'; background: transparent; }
@media (min-width: 901px) { html.skin-grimoire .shell.skinned { padding-left: 232px; } }
@media (max-width: 900px) and (min-width: 641px) { html.skin-grimoire .shell.skinned { padding-left: 72px; } }
@media (max-width: 640px) { html.skin-grimoire .shell.skinned { --tabbar: calc(56px + env(safe-area-inset-bottom)); } }
/* icons drawn like pen strokes: a touch finer, square-ish ends */
html.skin-grimoire svg.icon { stroke-width: 1.5; stroke-linecap: butt; stroke-linejoin: miter; }
html.skin-grimoire .btn { border-radius: 3px; border-color: color-mix(in srgb, var(--warn) 30%, transparent); font-family: inherit; }
html.skin-grimoire .btn.primary { background: var(--accent); border-color: var(--accent); color: var(--text); }
html.skin-grimoire .chip, html.skin-grimoire .seg { border-radius: 3px; }
html.skin-grimoire .chip.on { background: color-mix(in srgb, var(--accent) 22%, transparent); color: var(--text); border-color: var(--accent); }
html.skin-grimoire .seg > button.on { background: color-mix(in srgb, var(--accent) 24%, transparent); color: var(--text); }
html.skin-grimoire .pill { border-radius: 2px; }
html.skin-grimoire .sec { letter-spacing: .14em; text-transform: uppercase; font-size: 13px; color: var(--warn); }
html.skin-grimoire :is(input:not([type="checkbox"]):not([type="radio"]):not([type="range"]), select, textarea) { border-radius: 3px; border-color: color-mix(in srgb, var(--warn) 22%, var(--line)); }
html.skin-grimoire :is(input, select, textarea):focus-visible { outline: 1px solid var(--warn); }
/* page change: a quiet fade */
html.skin-grimoire .skin-grimoire-leave-active { transition: opacity 120ms ease-in; }
html.skin-grimoire .skin-grimoire-enter-active { transition: opacity 220ms ease-out; }
html.skin-grimoire .skin-grimoire-leave-to, html.skin-grimoire .skin-grimoire-enter-from { opacity: 0; }
</style>
