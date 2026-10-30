<script setup lang="ts">
/**
 * Disco page tabs: a mixing-desk row; each tab has a little equaliser under it, flat when idle, dancing under
 * the open one (whose label glows). Same behaviour as the stock PageTabs: sticky, sideways scroll on a phone
 * with the open tab kept in view, badges visible.
 */
const props = defineProps<{ tabs: { key: string, label: string, icon?: string, badge?: number | string, tone?: 'ok' | 'warn' | 'bad' }[] }>()
const model = defineModel<string>({ required: true })
const anchor = ref<HTMLElement>()
const strip = ref<HTMLElement>()
const edge = ref({ l: false, r: false })
const BARS = [0.55, 0.38, 0.72, 0.47, 0.63, 0.41, 0.69]

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
  <div class="dpt-wrap">
    <div ref="anchor" />
    <nav class="dpt" :class="{ l: edge.l, r: edge.r }">
      <div ref="strip" class="strip" role="tablist" @scroll.passive="measure">
        <button
          v-for="t in tabs" :key="t.key" type="button" role="tab" class="pt" :class="{ on: model === t.key }"
          :aria-selected="model === t.key" @click="pick(t.key)"
        >
          <span class="top">
            <Icon v-if="t.icon" :name="t.icon" :size="15" />
            <span>{{ t.label }}</span>
            <span v-if="t.badge" class="bdg" :class="t.tone ?? 'warn'">{{ t.badge }}</span>
          </span>
          <span class="eq" aria-hidden="true">
            <i v-for="(b, i) in BARS" :key="i" :style="{ '--h': b, animationDuration: `${0.42 + (i % 4) * 0.13}s` }" />
          </span>
        </button>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.dpt-wrap { display: contents; }
.dpt {
  position: sticky; top: var(--ptabs-top, env(safe-area-inset-top, 0px)); z-index: 20; margin: 0 0 18px;
  background: linear-gradient(180deg, rgba(20, 8, 36, .96), rgba(13, 6, 24, .92));
  border-bottom: 1px solid rgba(255, 63, 180, .35); border-radius: 0 0 12px 12px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, .35);
}
.strip { display: flex; gap: 4px; overflow-x: auto; scrollbar-width: none; padding: 6px 4px 4px; overscroll-behavior-x: contain; }
.strip::-webkit-scrollbar { display: none; }
.dpt.l .strip { mask-image: linear-gradient(to right, transparent, rgba(0, 0, 0, 1) 28px); }
.dpt.r .strip { mask-image: linear-gradient(to left, transparent, rgba(0, 0, 0, 1) 28px); }
.dpt.l.r .strip { mask-image: linear-gradient(to right, transparent, rgba(0, 0, 0, 1) 28px, rgba(0, 0, 0, 1) calc(100% - 28px), transparent); }
.pt {
  flex: none; display: flex; flex-direction: column; align-items: stretch; gap: 3px; min-height: 40px; padding: 5px 12px 3px;
  font: inherit; font-size: 13px; font-weight: 700; color: var(--muted); white-space: nowrap; cursor: pointer;
  background: none; border: 0; border-radius: 10px; -webkit-tap-highlight-color: transparent; transition: background .2s, color .2s;
}
.pt:hover { color: var(--text); background: rgba(255, 255, 255, .04); }
.top { display: inline-flex; align-items: center; justify-content: center; gap: 6px; }
.pt.on { color: var(--text); background: rgba(255, 63, 180, .12); text-shadow: 0 0 10px rgba(255, 63, 180, .8); }
.eq { display: flex; align-items: flex-end; justify-content: center; gap: 2px; height: 9px; }
.eq i { width: 4px; height: 100%; border-radius: 1px; background: var(--line-2); transform-origin: bottom; transform: scaleY(.22); }
.pt.on .eq i {
  background: linear-gradient(0deg, var(--ok), var(--warn) 60%, var(--accent));
  animation: eqd .5s ease-in-out infinite alternate;
}
@keyframes eqd { from { transform: scaleY(.2); } to { transform: scaleY(var(--h)); } }
.pt.on .eq i:nth-child(odd) { animation-direction: alternate-reverse; }
.bdg { min-width: 18px; padding: 0 5px; font-size: 11px; font-weight: 900; line-height: 17px; text-align: center; text-shadow: none; color: var(--bg); background: var(--warn); border-radius: 999px; }
.bdg.bad { background: var(--bad); color: var(--text); }
.bdg.ok { background: var(--ok); }
@media (max-width: 640px) {
  .dpt { margin-left: -12px; margin-right: -12px; border-radius: 0; }
  .pt { min-height: 44px; padding: 7px 12px 4px; }
}
@media (prefers-reduced-motion: reduce) {
  .pt.on .eq i { animation: none; transform: scaleY(var(--h)); }
  .pt { transition: none; }
}
</style>
