<script setup lang="ts">
/**
 * Page tabs as a tmux status line: `[page] 1:metrics* 2:media- 3:disks`, the open window inverted, the last
 * one marked "-". Alt+1…9 switches windows like tmux (only when not typing). Sticky under the window title bar,
 * sideways scroll on a phone with the open tab kept in view.
 */
const props = defineProps<{ tabs: { key: string, label: string, icon?: string, badge?: number | string, tone?: 'ok' | 'warn' | 'bad' }[] }>()
const model = defineModel<string>({ required: true })
const route = useRoute()
const session = computed(() => route.path.replace(/^\/+/, '').split('/')[0] || '~')
const anchor = ref<HTMLElement>()
const strip = ref<HTMLElement>()
const prev = ref('')
const name = (l: string) => l.toLowerCase().replace(/\s+/g, '-')

function reveal(smooth = true) {
  const s = strip.value
  const b = s?.querySelector<HTMLElement>('.on')
  if (!s || !b) return
  s.scrollTo({ left: Math.max(0, b.offsetLeft - (s.clientWidth - b.offsetWidth) / 2), behavior: smooth ? 'smooth' : 'auto' })
}
function pick(k: string) {
  if (k === model.value) return
  prev.value = model.value
  model.value = k
  const a = anchor.value
  const stick = parseFloat(getComputedStyle(a?.nextElementSibling ?? document.body).top) || 0
  const y = a?.getBoundingClientRect().top ?? 0
  if (a && y < stick) window.scrollTo({ top: window.scrollY + y - stick })
}
function onKey(e: KeyboardEvent) {
  if (!e.altKey || e.ctrlKey || e.metaKey) return
  const el = e.target as HTMLElement | null
  if (el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName))) return
  const i = Number(e.key) - 1
  const t = Number.isInteger(i) && i >= 0 ? props.tabs[i] : undefined
  if (t) { e.preventDefault(); pick(t.key) }
}
watch(model, () => nextTick(() => reveal()))
onMounted(() => { nextTick(() => reveal(false)); window.addEventListener('keydown', onKey) })
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="tpt-wrap">
    <div ref="anchor" />
    <nav class="tpt">
      <span class="ses">{{ `[${session}]` }}</span>
      <div ref="strip" class="strip" role="tablist">
        <button
          v-for="(t, i) in tabs" :key="t.key" type="button" role="tab" class="pt" :class="{ on: model === t.key }"
          :aria-selected="model === t.key" @click="pick(t.key)"
        >
          <span class="ix">{{ i + 1 }}:</span><span>{{ name(t.label) }}</span><span class="fl">{{ model === t.key ? '*' : prev === t.key ? '-' : ' ' }}</span>
          <span v-if="t.badge" class="bdg" :class="t.tone ?? 'warn'">{{ `(${t.badge})` }}</span>
        </button>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.tpt-wrap { display: contents; }
.tpt {
  position: sticky; top: var(--ptabs-top, 0px); z-index: 20; display: flex; align-items: stretch; margin: 0 0 16px;
  background: color-mix(in srgb, var(--accent) 16%, var(--bg)); border-top: 1px solid var(--line-2); border-bottom: 1px solid var(--line-2);
  font-family: var(--tm-mono); font-size: 13.5px; box-shadow: 0 6px 16px rgba(0, 0, 0, .45);
}
.ses { flex: none; display: flex; align-items: center; padding: 0 10px; background: var(--accent); color: var(--bg); font-weight: 700; text-shadow: none; }
.strip { flex: 1; min-width: 0; display: flex; overflow-x: auto; scrollbar-width: none; overscroll-behavior-x: contain; }
.strip::-webkit-scrollbar { display: none; }
.pt {
  flex: none; display: inline-flex; align-items: center; min-height: 36px; padding: 0 10px; border: 0; background: none;
  color: var(--muted); font: inherit; white-space: pre; cursor: pointer; -webkit-tap-highlight-color: transparent;
}
.pt:hover { color: var(--text); background: color-mix(in srgb, var(--accent) 12%, transparent); }
.pt.on { background: var(--text); color: var(--bg); font-weight: 700; text-shadow: none; }
.ix { opacity: .75; }
.bdg { margin-left: 4px; font-weight: 700; color: var(--warn); }
.bdg.bad { color: var(--bad); }
.bdg.ok { color: var(--ok); }
.pt.on .bdg { color: var(--bg); }
@media (max-width: 640px) {
  .tpt { margin-left: -12px; margin-right: -12px; }
  .ses { padding: 0 8px; max-width: 30%; overflow: hidden; }
  .pt { min-height: 40px; }
}
</style>
