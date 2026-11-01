<script setup lang="ts">
/**
 * A page's own sections as a row of squishy candy pills (like the skin's buttons: white, pink rim, a little 3D
 * ledge), the open one filled pink with a heart and a jelly wobble when picked. Sticky at the top on a soft frosted
 * strip with a dashed seam, scrolls sideways on a phone with the open tab kept in view.
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
  // scrolled past the bar: bring the new section's start up under it instead of leaving you mid-page
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
  <div class="kt-wrap">
    <div ref="anchor" />
    <nav class="kt" :class="{ l: edge.l, r: edge.r }">
      <div ref="strip" class="strip" role="tablist" @scroll.passive="measure">
        <button
          v-for="t in tabs" :key="t.key" type="button" role="tab" class="tab" :class="{ on: model === t.key }"
          :aria-selected="model === t.key" @click="pick(t.key)"
        >
          <span v-if="model === t.key" class="hrt" aria-hidden="true">{{ '♥' }}</span>
          <Icon v-else-if="t.icon" :name="t.icon" :size="16" />
          <span>{{ t.label }}</span>
          <span v-if="t.badge" class="bdg" :class="t.tone ?? 'warn'">{{ t.badge }}</span>
        </button>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.kt-wrap { display: contents; }
.kt {
  position: sticky; top: var(--ptabs-top, env(safe-area-inset-top, 0px)); z-index: 20; margin: 0 0 14px;
  background: color-mix(in srgb, var(--bg) 86%, transparent); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  border-bottom: 2px dashed color-mix(in srgb, var(--accent) 28%, transparent);
}
.strip { display: flex; align-items: center; gap: 8px; overflow-x: auto; scrollbar-width: none; padding: 8px 4px 11px; overscroll-behavior-x: contain; }
.strip::-webkit-scrollbar { display: none; }
.kt.l .strip { mask-image: linear-gradient(to right, transparent, black 28px); }
.kt.r .strip { mask-image: linear-gradient(to left, transparent, black 28px); }
.kt.l.r .strip { mask-image: linear-gradient(to right, transparent, black 28px, black calc(100% - 28px), transparent); }
.tab {
  flex: none; display: inline-flex; align-items: center; gap: 6px; min-height: 38px; padding: 0 16px; border-radius: 999px;
  font: inherit; font-size: 13.5px; font-weight: 800; white-space: nowrap; color: var(--muted); cursor: pointer;
  background: var(--panel); border: 2px solid var(--line-2); box-shadow: 0 3px 0 var(--line-2);
  -webkit-tap-highlight-color: transparent; transition: transform .12s, box-shadow .12s, background .2s, color .2s;
}
.tab:hover { color: var(--accent); }
.tab:active { transform: translateY(2px); box-shadow: 0 1px 0 var(--line-2); }
.tab:focus-visible { outline: none; box-shadow: 0 3px 0 var(--line-2), 0 0 0 4px color-mix(in srgb, var(--accent) 22%, transparent); }
.tab.on {
  color: var(--panel); background: var(--accent); border-color: color-mix(in srgb, var(--accent) 85%, var(--text));
  box-shadow: 0 3px 0 color-mix(in srgb, var(--accent) 85%, var(--text)); animation: kt-jelly .55s;
}
.hrt { font-size: 14px; line-height: 1; }
.bdg {
  min-width: 18px; padding: 0 5px; border-radius: 9px; font-size: 10.5px; font-weight: 800; line-height: 16px; text-align: center;
  color: var(--panel); background: var(--warn); border: 1px solid var(--panel);
}
.bdg.bad { background: var(--bad); }
.bdg.ok { background: var(--ok); }
@keyframes kt-jelly { 0% { transform: scale(1, 1); } 30% { transform: scale(1.12, .88); } 50% { transform: scale(.94, 1.08); } 70% { transform: scale(1.04, .97); } 100% { transform: scale(1, 1); } }
@media (max-width: 640px) {
  .kt { margin-left: -12px; margin-right: -12px; }
  .strip { padding-left: 10px; padding-right: 10px; }
  .tab { padding: 0 14px; }
}
@media (prefers-reduced-motion: reduce) {
  .tab { transition: none; }
  .tab.on { animation: none; }
}
</style>
