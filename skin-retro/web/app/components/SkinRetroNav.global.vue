<script setup lang="ts">
/**
 * The layout's navigation as a taskbar (bottom, phone and desktop alike): Start opens a menu with every page,
 * the pinned pages sit on the bar as quick-launch buttons (the viewer's pick, "Edit tabs" in the menu), the current
 * page as its task, the tray has jobs, search, live state and a clock.
 * Props are the layout's own (layouts/default.vue → useSkinned('Nav')).
 */
const props = withDefaults(defineProps<{
  nav?: { to: string, icon: string, label: string }[], path?: string
  badge?: (to: string) => number, mark?: (to: string) => string
  state?: string, stateText?: string, up?: string, full?: boolean
}>(), { nav: () => [], path: '/', badge: () => 0, mark: () => '', state: 'ok', stateText: '', up: '', full: false })
const emit = defineEmits<{ search: [] }>()
const open = ref(false)
const here = computed(() => props.nav.find(n => n.to === props.path))
const totalBadge = computed(() => props.nav.reduce((s, n) => s + (props.badge(n.to) || 0), 0))
const { pinned, isPinned, toggle, editing, full: pinsFull, max, keys } = useNavPins(() => props.nav)
const task = computed(() => (here.value && !isPinned(here.value.to) ? here.value : null))
watch(() => props.path, () => (open.value = false))
watch(open, v => { if (!v) editing.value = false })
function go(to: string) { if (editing.value) return toggle(to); open.value = false; navigateTo(to) }

const now = ref(new Date())
let t: ReturnType<typeof setInterval> | undefined
onMounted(() => (t = setInterval(() => (now.value = new Date()), 15_000)))
onUnmounted(() => clearInterval(t))
const clock = computed(() => now.value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') open.value = false }
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="retro-nav">
    <div v-if="open" class="scrim" @click="open = false" />
    <div v-if="open" class="menu" role="menu">
      <div class="stripe"><span>{{ 'bastion' }}</span></div>
      <div class="items">
        <div v-if="editing" class="hint">{{ $t('skinRetro.pinHint', { n: keys.length, max }) }}</div>
        <button v-for="n in nav" :key="n.to" type="button" :role="editing ? 'menuitemcheckbox' : 'menuitem'" :aria-checked="editing ? isPinned(n.to) : undefined" class="item" :class="{ on: n.to === path && !editing, dim: editing && pinsFull && !isPinned(n.to) }" @click="go(n.to)">
          <span v-if="editing" class="chk">{{ isPinned(n.to) ? '✓' : '' }}</span>
          <Icon :name="n.icon" :size="18" /><span class="l">{{ n.label }}</span>
          <span v-if="badge(n.to)" class="badge">{{ badge(n.to) }}</span>
          <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
        </button>
        <hr>
        <button type="button" class="item" :aria-pressed="editing" @click="editing = !editing">
          <Icon name="pin" :size="18" /><span class="l">{{ editing ? $t('skinRetro.done') : $t('skinRetro.editTabs') }}</span>
        </button>
        <button type="button" class="item" @click="open = false; emit('search')">
          <Icon name="search" :size="18" /><span class="l">{{ $t('skinRetro.search') }}</span>
        </button>
      </div>
    </div>
    <nav class="bar">
      <button type="button" class="start" :class="{ down: open }" :aria-expanded="open" @click="open = !open">
        <Icon name="grid" :size="16" /><b>{{ $t('skinRetro.start') }}</b>
        <span v-if="totalBadge" class="badge">{{ totalBadge }}</span>
      </button>
      <span class="quick">
        <NuxtLink v-for="n in pinned" :key="n.to" :to="n.to" class="ql" :class="{ on: n.to === path }" :title="n.label" :aria-label="n.label">
          <Icon :name="n.icon" :size="16" />
          <span v-if="badge(n.to)" class="badge">{{ badge(n.to) }}</span>
          <span v-else-if="mark(n.to)" class="cm" :class="mark(n.to)" />
        </NuxtLink>
      </span>
      <span v-if="task" class="task"><Icon :name="task.icon" :size="15" /><span class="l">{{ task.label }}</span></span>
      <span class="tray">
        <JobsButton />
        <button type="button" class="tb" :aria-label="$t('skinRetro.search')" @click="emit('search')"><Icon name="search" :size="15" /></button>
        <span class="dot" :class="state" />
        <span class="up">{{ up }}</span>
        <span class="clock">{{ clock }}</span>
      </span>
    </nav>
  </div>
</template>

<style scoped>
.bar { position: fixed; left: 0; right: 0; bottom: 0; z-index: 60; display: flex; align-items: center; gap: 6px; height: calc(40px + env(safe-area-inset-bottom)); padding: 3px 4px calc(3px + env(safe-area-inset-bottom)); background: var(--panel); border-top: 2px solid var(--line-2); box-shadow: 0 -1px 0 var(--panel-2); }
.start, .task, .tb { display: inline-flex; align-items: center; gap: 6px; height: 32px; padding: 0 10px; font: inherit; color: var(--text); background: var(--panel); border: 2px solid; border-color: var(--line-2) var(--text) var(--text) var(--line-2); cursor: pointer; }
.start.down { border-color: var(--text) var(--line-2) var(--line-2) var(--text); background: var(--panel-2); }
.task { min-width: 0; max-width: 40vw; border-color: var(--text) var(--line-2) var(--line-2) var(--text); background: var(--panel-2); font-weight: 700; cursor: default; }
.task .l { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.quick { display: flex; align-items: center; gap: 2px; padding: 0 4px; border-left: 1px solid var(--line); border-right: 1px solid var(--line-2); flex: none; }
.ql { position: relative; display: grid; place-items: center; width: 30px; height: 30px; color: var(--text); border: 2px solid transparent; }
.ql:hover, .ql:focus-visible { border-color: var(--line-2) var(--text) var(--text) var(--line-2); outline: none; }
.ql.on { border-color: var(--text) var(--line-2) var(--line-2) var(--text); background: var(--panel-2); }
.ql .badge, .ql .cm { position: absolute; top: -3px; right: -3px; }
.hint { padding: 4px 10px 6px; font-size: 12px; color: var(--muted); border-bottom: 1px solid var(--line); margin-bottom: 3px; }
.chk { width: 14px; height: 14px; flex: none; display: grid; place-items: center; font-size: 12px; font-weight: 700; line-height: 1; background: var(--line-2); color: var(--text); border: 2px solid; border-color: var(--text) var(--line-2) var(--line-2) var(--text); }
.item.dim { opacity: .45; }
.tray { margin-left: auto; display: flex; align-items: center; gap: 8px; height: 32px; padding: 0 8px; border: 2px solid; border-color: var(--line) var(--line-2) var(--line-2) var(--line); font-size: 12px; }
.tray .tb { height: 26px; padding: 0 6px; }
.up { color: var(--muted); }
.dot { width: 9px; height: 9px; border-radius: 50%; background: var(--ok); }
.dot.warn { background: var(--warn); } .dot.bad { background: var(--bad); }
.badge { min-width: 16px; padding: 0 4px; font-size: 11px; line-height: 16px; text-align: center; color: var(--line-2); background: var(--bad); }
.scrim { position: fixed; inset: 0; z-index: 61; }
.menu { position: fixed; left: 4px; bottom: calc(42px + env(safe-area-inset-bottom)); z-index: 62; display: flex; width: min(300px, calc(100vw - 8px)); max-height: calc(100dvh - 60px); background: var(--panel); border: 2px solid; border-color: var(--line-2) var(--text) var(--text) var(--line-2); box-shadow: 2px 2px 0 var(--text); }
.stripe { width: 28px; flex: none; display: flex; align-items: flex-end; justify-content: center; padding-bottom: 8px; background: linear-gradient(0deg, var(--accent), color-mix(in srgb, var(--accent) 50%, var(--text))); }
.stripe span { writing-mode: vertical-rl; transform: rotate(180deg); color: var(--line-2); font-weight: 700; font-size: 17px; letter-spacing: 1px; }
.items { flex: 1; overflow-y: auto; padding: 3px; }
.item { display: flex; align-items: center; gap: 10px; width: 100%; min-height: 36px; padding: 4px 10px; border: 0; background: none; color: var(--text); font: inherit; text-align: left; cursor: pointer; }
.item:hover, .item:focus-visible, .item.on { background: var(--accent); color: var(--line-2); outline: none; }
.item .l { flex: 1; }
.cm { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); }
.cm.input { background: var(--warn); }
hr { border: 0; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line-2); margin: 3px 0; }
@media (max-width: 640px) {
  .up, .clock { display: none; }
  .start b { display: none; }
  .task .l { display: none; }
  .quick { gap: 1px; padding: 0 2px; }
  .ql { width: 34px; height: 32px; }
}
@media (pointer: coarse) { .tray .tb { height: 30px; min-width: 34px; justify-content: center; } }
</style>

<style>
/* the page makes room for the taskbar; only while this skin is on */
html.skin-retro .shell.skinned { --tabbar: calc(44px + env(safe-area-inset-bottom)); }
html.skin-retro main.wrap { padding-bottom: calc(60px + env(safe-area-inset-bottom)); }
html.skin-retro .grid, html.skin-retro .stack { gap: 10px; }
/* chunky pixel icons: square ends, mitred corners, no anti-aliased curves where it can be helped */
html.skin-retro svg.icon { stroke-width: 2.2; stroke-linecap: square; stroke-linejoin: miter; shape-rendering: crispEdges; }
</style>
