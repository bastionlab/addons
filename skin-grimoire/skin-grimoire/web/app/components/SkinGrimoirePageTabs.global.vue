<script setup lang="ts">
/**
 * Grimoire page tabs: chapter headings in gold small caps along a ruled line; the open one is underlined in
 * crimson. Same behaviour as the stock PageTabs: sticky, sideways scroll on a phone with the open tab kept in view.
 */
const props = defineProps<{ tabs: { key: string, label: string, icon?: string, badge?: number | string, tone?: 'ok' | 'warn' | 'bad' }[] }>()
const model = defineModel<string>({ required: true })
const anchor = ref<HTMLElement>()
const strip = ref<HTMLElement>()

function reveal(smooth = true) {
  const s = strip.value
  const b = s?.querySelector<HTMLElement>('.on')
  if (!s || !b) return
  const left = b.offsetLeft - (s.clientWidth - b.offsetWidth) / 2
  s.scrollTo({ left: Math.max(0, left), behavior: smooth ? 'smooth' : 'auto' })
}
function pick(k: string) {
  if (k === model.value) return
  model.value = k
  // scrolled past the bar: bring the new section's start up under it instead of leaving you mid-page
  const a = anchor.value
  const stick = parseFloat(getComputedStyle(a?.nextElementSibling ?? document.body).top) || 0
  const y = a?.getBoundingClientRect().top ?? 0
  if (a && y < stick) window.scrollTo({ top: window.scrollY + y - stick })
}
watch(model, () => nextTick(() => reveal()))
onMounted(() => nextTick(() => reveal(false)))
watch(() => props.tabs.length, () => nextTick(() => reveal(false)))
</script>

<template>
  <div class="mpt-wrap">
    <div ref="anchor" />
    <nav class="mpt">
      <div ref="strip" class="strip" role="tablist">
        <button
          v-for="t in tabs" :key="t.key" type="button" role="tab" class="tb" :class="{ on: model === t.key }"
          :aria-selected="model === t.key" @click="pick(t.key)"
        >
          <Icon v-if="t.icon" :name="t.icon" :size="15" />
          <span>{{ t.label }}</span>
          <span v-if="t.badge" class="bdg" :class="t.tone ?? 'warn'">{{ t.badge }}</span>
        </button>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.mpt-wrap { display: contents; }
.mpt {
  position: sticky; top: var(--ptabs-top, env(safe-area-inset-top, 0px)); z-index: 20; margin: 0 0 18px;
  font-family: Georgia, "Palatino Linotype", Palatino, serif;
  background: color-mix(in srgb, var(--bg) 94%, transparent);
  border-bottom: 1px solid color-mix(in srgb, var(--warn) 28%, transparent);
}
.strip { display: flex; gap: 2px; overflow-x: auto; scrollbar-width: none; overscroll-behavior-x: contain; }
.strip::-webkit-scrollbar { display: none; }
.tb {
  flex: none; display: inline-flex; align-items: center; gap: 7px; min-height: 40px; padding: 6px 14px;
  font: inherit; font-size: 12px; letter-spacing: .13em; text-transform: uppercase; white-space: nowrap; cursor: pointer;
  color: var(--muted); background: none; border: 0; border-bottom: 2px solid transparent; margin-bottom: -1px;
  -webkit-tap-highlight-color: transparent;
}
.tb:hover { color: var(--text); }
.tb.on { color: var(--warn); border-bottom-color: var(--accent); }
.bdg { min-width: 18px; padding: 0 5px; border-radius: 2px; font: 700 10.5px/17px system-ui, sans-serif; letter-spacing: 0; text-align: center; background: var(--warn); color: var(--bg); }
.bdg.bad { background: var(--bad); color: var(--text); }
.bdg.ok { background: var(--ok); color: var(--bg); }
@media (max-width: 640px) { .mpt { margin-left: -12px; margin-right: -12px; } .strip { padding: 0 6px; } .tb { padding: 6px 11px; letter-spacing: .09em; } }
</style>
