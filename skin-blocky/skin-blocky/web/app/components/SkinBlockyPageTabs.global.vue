<script setup lang="ts">
/**
 * Creative-inventory tabs: square stone tabs standing on top of a GUI window edge; the open one is raised, lighter
 * and merges into the window below. Same behaviour as the stock PageTabs: sticky, sideways scroll on a phone with
 * the open tab kept in view, badges visible.
 */
const props = defineProps<{ tabs: { key: string, label: string, icon?: string, badge?: number | string, tone?: 'ok' | 'warn' | 'bad' }[] }>()
const model = defineModel<string>({ required: true })
const anchor = ref<HTMLElement>()
const strip = ref<HTMLElement>()
const edge = ref({ l: false, r: false })

function measure() {
  const s = strip.value
  if (s) edge.value = { l: s.scrollLeft > 4, r: s.scrollLeft + s.clientWidth < s.scrollWidth - 4 }
}
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
  const a = anchor.value
  const stick = parseFloat(getComputedStyle(a?.nextElementSibling ?? document.body).top) || 0
  const y = a?.getBoundingClientRect().top ?? 0
  if (a && y < stick) window.scrollTo({ top: window.scrollY + y - stick })
}
watch(model, () => nextTick(() => reveal()))
onMounted(() => { nextTick(() => { reveal(false); measure() }); window.addEventListener('resize', measure) })
onBeforeUnmount(() => window.removeEventListener('resize', measure))
watch(() => props.tabs.length, () => nextTick(measure))
</script>

<template>
  <div class="bpt-wrap">
    <div ref="anchor" />
    <nav class="bpt" :class="{ l: edge.l, r: edge.r }">
      <div ref="strip" class="strip" role="tablist" @scroll.passive="measure">
        <button
          v-for="t in tabs" :key="t.key" type="button" role="tab" class="pt" :class="{ on: model === t.key }"
          :aria-selected="model === t.key" @click="pick(t.key)"
        >
          <Icon v-if="t.icon" :name="t.icon" :size="16" class="ic" />
          <span>{{ t.label }}</span>
          <span v-if="t.badge" class="bdg" :class="t.tone ?? 'warn'">{{ t.badge }}</span>
        </button>
      </div>
      <i class="edge" aria-hidden="true" />
    </nav>
  </div>
</template>

<style scoped>
.bpt-wrap { display: contents; }
.bpt { position: sticky; top: var(--ptabs-top, env(safe-area-inset-top, 0px)); z-index: 20; margin: 0 0 16px; padding-top: 4px; }
.strip { position: relative; z-index: 1; display: flex; align-items: flex-end; gap: 3px; overflow-x: auto; scrollbar-width: none; padding: 0 4px; overscroll-behavior-x: contain; }
.strip::-webkit-scrollbar { display: none; }
.bpt.l .strip { mask-image: linear-gradient(to right, transparent, rgba(0, 0, 0, 1) 24px); }
.bpt.r .strip { mask-image: linear-gradient(to left, transparent, rgba(0, 0, 0, 1) 24px); }
.bpt.l.r .strip { mask-image: linear-gradient(to right, transparent, rgba(0, 0, 0, 1) 24px, rgba(0, 0, 0, 1) calc(100% - 24px), transparent); }
.pt {
  position: relative; flex: none; display: inline-flex; align-items: center; gap: 6px; min-height: 36px; padding: 6px 11px 4px; margin-bottom: 0;
  font-family: "Courier New", Courier, monospace; font-size: 13px; font-weight: 900; text-transform: uppercase; white-space: nowrap; cursor: pointer;
  color: var(--muted); text-shadow: 2px 2px 0 rgba(40, 40, 40, 1);
  background: rgba(78, 78, 78, 1); border: 2px solid rgba(0, 0, 0, 1); border-bottom: 0;
  box-shadow: inset 2px 2px 0 rgba(130, 130, 130, 1), inset -2px 0 0 rgba(40, 40, 40, 1);
  -webkit-tap-highlight-color: transparent;
}
.pt:hover { color: var(--text); }
.ic { filter: drop-shadow(1px 1px 0 rgba(40, 40, 40, 1)); }
.pt.on {
  z-index: 2; min-height: 42px; padding-bottom: 8px; margin-bottom: -4px; color: var(--text); background: var(--panel);
  box-shadow: inset 3px 3px 0 rgba(255, 255, 255, .32), inset -3px 0 0 rgba(0, 0, 0, .38);
}
.edge {
  position: relative; display: block; height: 10px; background: var(--panel); border: 2px solid rgba(0, 0, 0, 1);
  box-shadow: inset 0 3px 0 rgba(255, 255, 255, .32), 0 3px 0 rgba(0, 0, 0, .25);
}
.bdg { min-width: 18px; padding: 0 4px; font-size: 12px; line-height: 16px; text-align: center; text-shadow: none; color: rgba(0, 0, 0, 1); background: var(--warn); border: 1px solid rgba(0, 0, 0, 1); }
.bdg.bad { background: var(--bad); }
.bdg.ok { background: var(--ok); }
@media (max-width: 640px) {
  .bpt { margin-left: -12px; margin-right: -12px; }
  .pt { min-height: 38px; }
  .pt.on { min-height: 44px; }
}
</style>
