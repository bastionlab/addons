<script setup lang="ts">
/**
 * Liquid Glass page tabs: a frosted capsule (like the phone tab bar) holding the sections; the open one is a
 * brighter glass pill that springs in. Sticks just under the Frame's compact blurred header while scrolling.
 * Same behaviour as the stock PageTabs: sideways scroll on a phone with the open tab kept in view.
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
  <div class="gpt-wrap">
    <div ref="anchor" />
    <nav class="gpt" :class="{ l: edge.l, r: edge.r }">
      <div ref="strip" class="strip" role="tablist" @scroll.passive="measure">
        <button
          v-for="t in tabs" :key="t.key" type="button" role="tab" class="pt" :class="{ on: model === t.key }"
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
.gpt-wrap { display: contents; }
.gpt {
  position: sticky; top: calc(var(--ptabs-top, env(safe-area-inset-top, 0px)) + 8px); z-index: 20;
  width: fit-content; max-width: 100%; margin: 0 0 18px; padding: 4px; border-radius: 999px;
  background: linear-gradient(180deg, rgba(255, 255, 255, .13), rgba(255, 255, 255, .05));
  border: 1px solid rgba(255, 255, 255, .16);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .26), 0 12px 30px rgba(0, 0, 0, .4);
  backdrop-filter: blur(26px) saturate(190%); -webkit-backdrop-filter: blur(26px) saturate(190%);
}
.strip { display: flex; gap: 2px; overflow-x: auto; scrollbar-width: none; border-radius: 999px; overscroll-behavior-x: contain; }
.strip::-webkit-scrollbar { display: none; }
/* a soft fade on the side that has more tabs, so a phone shows there is more to swipe to */
.gpt.l .strip { mask-image: linear-gradient(to right, transparent, rgba(0, 0, 0, 1) 28px); }
.gpt.r .strip { mask-image: linear-gradient(to left, transparent, rgba(0, 0, 0, 1) 28px); }
.gpt.l.r .strip { mask-image: linear-gradient(to right, transparent, rgba(0, 0, 0, 1) 28px, rgba(0, 0, 0, 1) calc(100% - 28px), transparent); }
.pt {
  position: relative; z-index: 0; flex: none; display: inline-flex; align-items: center; gap: 6px; min-height: 36px; padding: 6px 15px;
  border: 0; border-radius: 999px; background: none; color: var(--muted); font: inherit; font-size: 13.5px; font-weight: 500; letter-spacing: -.01em;
  white-space: nowrap; cursor: pointer; -webkit-tap-highlight-color: transparent;
  transition: color .2s, transform .3s cubic-bezier(.34, 1.56, .64, 1);
}
/* the glass pill: always there, faded out; the open tab springs it in */
.pt::before {
  content: ''; position: absolute; inset: 0; z-index: -1; border-radius: inherit; pointer-events: none; opacity: 0; transform: scale(.82);
  background: linear-gradient(180deg, rgba(255, 255, 255, .26), rgba(255, 255, 255, .1));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .38), 0 4px 14px rgba(0, 0, 0, .28);
  transition: opacity .25s, transform .45s cubic-bezier(.34, 1.45, .64, 1);
}
.pt:hover { color: var(--text); }
.pt:active { transform: scale(.94); }
.pt.on { color: var(--text); font-weight: 650; }
.pt.on::before { opacity: 1; transform: none; }
.pt.on .icon { color: var(--accent); filter: drop-shadow(0 0 6px color-mix(in srgb, var(--accent) 70%, transparent)); }
.bdg {
  min-width: 18px; height: 18px; padding: 0 5px; border-radius: 999px; font-size: 11px; font-weight: 700; line-height: 18px; text-align: center;
  background: var(--warn); color: var(--bg); box-shadow: 0 2px 6px rgba(0, 0, 0, .35);
}
.bdg.bad { background: var(--bad); color: var(--text); }
.bdg.ok { background: var(--ok); }
@media (max-width: 640px) {
  .gpt { top: calc(var(--ptabs-top, env(safe-area-inset-top, 0px)) + 6px); margin-left: -4px; margin-right: -4px; max-width: calc(100% + 8px); }
  .pt { padding: 8px 13px; min-height: 38px; }
}
@media (prefers-reduced-motion: reduce) { .pt, .pt::before { transition: none; } }
</style>
