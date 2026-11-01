<script setup lang="ts">
/**
 * Comic Book page tabs: a row of chunky ink-bordered captions on a halftone strip with a heavy rule under it.
 * The open section is the yellow one, lifted with a hard shadow; pressing a caption punches it into the page.
 * Same behaviour as the stock PageTabs: sticky, sideways scroll on a phone with the open tab kept in view.
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
  <div class="cpt-wrap">
    <div ref="anchor" />
    <nav class="cpt" :class="{ l: edge.l, r: edge.r }">
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
.cpt-wrap { display: contents; }
.cpt {
  position: sticky; top: var(--ptabs-top, env(safe-area-inset-top, 0px)); z-index: 20; margin: 0 0 18px;
  background-color: var(--bg);
  background-image: radial-gradient(circle, rgba(0, 0, 0, .1) 1px, transparent 1.4px); background-size: 7px 7px;
  border-bottom: 3px solid var(--line-2);
}
.strip { display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; padding: 8px 6px 10px 2px; overscroll-behavior-x: contain; }
.strip::-webkit-scrollbar { display: none; }
/* a soft fade on the side that has more tabs, so a phone shows there is more to swipe to */
.cpt.l .strip { mask-image: linear-gradient(to right, transparent, rgba(0, 0, 0, 1) 28px); }
.cpt.r .strip { mask-image: linear-gradient(to left, transparent, rgba(0, 0, 0, 1) 28px); }
.cpt.l.r .strip { mask-image: linear-gradient(to right, transparent, rgba(0, 0, 0, 1) 28px, rgba(0, 0, 0, 1) calc(100% - 28px), transparent); }
.pt {
  position: relative; flex: none; display: inline-flex; align-items: center; gap: 6px; min-height: 36px; padding: 6px 13px;
  font: inherit; font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: .02em; white-space: nowrap; cursor: pointer;
  color: var(--line-2); background: var(--panel); border: 2.5px solid var(--line-2); border-radius: 8px; box-shadow: 3px 3px 0 var(--line-2);
  transition: transform .08s, box-shadow .08s; -webkit-tap-highlight-color: transparent;
}
.pt:hover { background: var(--panel-2); }
.pt:active { transform: translate(2px, 2px); box-shadow: 1px 1px 0 var(--line-2); }
.pt.on {
  background: var(--comic-yellow, var(--panel-2)); font-weight: 900; font-style: italic;
  transform: rotate(-1.5deg) translateY(-1px); box-shadow: 4px 4px 0 var(--line-2);
}
.pt.on:active { transform: rotate(-1.5deg) translate(2px, 2px); box-shadow: 1px 1px 0 var(--line-2); }
.bdg {
  min-width: 18px; padding: 0 5px; font-size: 11px; font-weight: 900; font-style: normal; line-height: 15px; text-align: center;
  color: var(--panel); background: var(--warn); border: 2px solid var(--line-2); border-radius: 999px;
}
.bdg.bad { background: var(--bad); }
.bdg.ok { background: var(--ok); }
@media (max-width: 640px) {
  .cpt { margin-left: -12px; margin-right: -12px; padding: 0 8px; }
  .strip { gap: 7px; }
  .pt { padding: 7px 12px; min-height: 38px; }
}
@media (prefers-reduced-motion: reduce) { .pt { transition: none; } }
</style>
