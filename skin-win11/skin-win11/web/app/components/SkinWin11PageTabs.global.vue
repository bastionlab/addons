<script setup lang="ts">
/** the page's section tabs as a Fluent selector bar on an acrylic strip: quiet text tabs, the open one bold with the accent pill under it */
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
  <div class="w11-ptabs-wrap">
    <div ref="anchor" />
    <nav class="w11-ptabs" :class="{ l: edge.l, r: edge.r }">
      <div ref="strip" class="strip" role="tablist" @scroll.passive="measure">
        <button
          v-for="t in tabs" :key="t.key" type="button" role="tab" class="pv" :class="{ on: model === t.key }"
          :aria-selected="model === t.key" @click="pick(t.key)"
        >
          <Icon v-if="t.icon" :name="t.icon" :size="16" class="ic" />
          <span class="lb" :data-l="t.label">{{ t.label }}</span>
          <span v-if="t.badge" class="ib" :class="t.tone ?? 'warn'">{{ t.badge }}</span>
          <span class="pill" aria-hidden="true" />
        </button>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.w11-ptabs-wrap { display: contents; }
/* acrylic strip, like the taskbar: blurred page behind, a hairline under it */
.w11-ptabs {
  position: sticky; top: var(--ptabs-top, env(safe-area-inset-top, 0px)); z-index: 20; margin: 0 0 16px;
  border-radius: 8px; border: 1px solid rgba(255, 255, 255, .07);
  background: color-mix(in srgb, var(--panel) 72%, transparent); backdrop-filter: blur(28px) saturate(1.5); -webkit-backdrop-filter: blur(28px) saturate(1.5);
  box-shadow: 0 2px 6px rgba(0, 0, 0, .22);
}
.strip { display: flex; gap: 2px; overflow-x: auto; scrollbar-width: none; padding: 4px; overscroll-behavior-x: contain; }
.strip::-webkit-scrollbar { display: none; }
.w11-ptabs.l .strip { mask-image: linear-gradient(to right, transparent, black 28px); }
.w11-ptabs.r .strip { mask-image: linear-gradient(to left, transparent, black 28px); }
.w11-ptabs.l.r .strip { mask-image: linear-gradient(to right, transparent, black 28px, black calc(100% - 28px), transparent); }
/* Fluent selector bar: quiet text tabs, the open one bold with an accent pill under it */
.pv {
  position: relative; flex: none; display: inline-flex; align-items: center; gap: 7px; min-height: 36px; padding: 6px 14px 8px;
  border: 0; border-radius: 6px; background: transparent; color: var(--muted); font: inherit; font-size: 13.5px; white-space: nowrap;
  cursor: pointer; transition: background .15s, color .15s; -webkit-tap-highlight-color: transparent;
}
.pv:hover { background: rgba(255, 255, 255, .06); color: var(--text); }
.pv:active { background: rgba(255, 255, 255, .04); color: var(--faint); }
.pv:focus-visible { outline: 2px solid var(--text); outline-offset: -2px; }
.pv.on { color: var(--text); }
.pv.on .ic { color: var(--accent); }
/* reserve the bold width so the row does not jump when a tab opens */
.lb { display: inline-grid; }
.lb::after { content: attr(data-l); font-weight: 600; visibility: hidden; height: 0; overflow: hidden; }
.pv.on .lb { font-weight: 600; }
.pill {
  position: absolute; left: 50%; bottom: 2px; width: 16px; height: 3px; border-radius: 3px; background: var(--accent);
  opacity: 0; transform: translateX(-50%) scaleX(.25); transition: transform .3s cubic-bezier(.1, .9, .2, 1), opacity .15s;
}
.pv.on .pill { opacity: 1; transform: translateX(-50%) scaleX(1); }
.pv:active .pill { transform: translateX(-50%) scaleX(.6); }
/* InfoBadge */
.ib { min-width: 16px; padding: 0 5px; border-radius: 8px; font-size: 10.5px; font-weight: 600; line-height: 16px; text-align: center; color: var(--bg); background: var(--warn); }
.ib.bad { background: var(--bad); }
.ib.ok { background: var(--ok); }
@media (max-width: 640px) {
  .w11-ptabs { margin: 0 -6px 12px; }
  .pv { padding: 6px 12px 9px; min-height: 40px; }
}
@media (prefers-reduced-motion: reduce) { .pv, .pill { transition: none; } }
</style>
