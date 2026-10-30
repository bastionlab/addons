<script setup lang="ts">
/**
 * A page's own sections as a classic tab control: grey bevelled tabs standing on the dialog's white top edge, the
 * open tab raised a little and joined to the body below, a dotted focus box round its label. Sticky at the top,
 * scrolls sideways on a phone with the open tab kept in view.
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
  <div class="rt-wrap">
    <div ref="anchor" />
    <nav class="rt" :class="{ l: edge.l, r: edge.r }">
      <div ref="strip" class="strip" role="tablist" @scroll.passive="measure">
        <button
          v-for="t in tabs" :key="t.key" type="button" role="tab" class="tab" :class="{ on: model === t.key }"
          :aria-selected="model === t.key" @click="pick(t.key)"
        >
          <span class="in">
            <Icon v-if="t.icon" :name="t.icon" :size="15" />
            <span>{{ t.label }}</span>
            <span v-if="t.badge" class="bdg" :class="t.tone ?? 'warn'">{{ t.badge }}</span>
          </span>
        </button>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.rt-wrap { display: contents; }
.rt { position: sticky; top: var(--ptabs-top, env(safe-area-inset-top, 0px)); z-index: 20; margin: 0 0 10px; background: var(--bg); }
/* the white line is the top edge of the dialog body; the open tab covers it and joins the body */
.strip {
  display: flex; align-items: flex-end; gap: 0; height: 44px; padding: 4px 4px 0; overflow-x: auto; overflow-y: hidden;
  scrollbar-width: none; overscroll-behavior-x: contain; box-shadow: inset 0 -2px 0 var(--line-2);
}
.strip::-webkit-scrollbar { display: none; }
.rt.l .strip { mask-image: linear-gradient(to right, transparent, black 28px); }
.rt.r .strip { mask-image: linear-gradient(to left, transparent, black 28px); }
.rt.l.r .strip { mask-image: linear-gradient(to right, transparent, black 28px, black calc(100% - 28px), transparent); }
.tab {
  position: relative; flex: none; display: inline-flex; align-items: center; height: 36px; margin: 0 -1px 2px 0; padding: 0 12px;
  font: inherit; font-family: Tahoma, "MS Sans Serif", Verdana, system-ui, sans-serif; font-size: 13px; color: var(--text); white-space: nowrap;
  background: var(--panel); border: 2px solid; border-bottom: 0; border-color: var(--line-2) var(--text) transparent var(--line-2);
  border-radius: 4px 4px 0 0; box-shadow: inset -1px 0 0 var(--line); cursor: pointer; -webkit-tap-highlight-color: transparent;
}
.tab:hover { background: var(--panel-2); }
.tab.on {
  z-index: 1; height: 40px; margin: 0 -3px 0 -2px; padding: 0 14px 2px; font-weight: 700; background: var(--panel);
}
.tab:first-child.on { margin-left: 0; }
.in { display: inline-flex; align-items: center; gap: 6px; padding: 1px 3px; border: 1px dotted transparent; }
.tab.on .in { border-color: var(--text); }
.tab:focus-visible { outline: none; }
.tab:focus-visible .in { border-color: var(--text); }
.bdg { min-width: 16px; padding: 0 4px; font-size: 11px; font-weight: 700; line-height: 16px; text-align: center; color: var(--line-2); background: var(--warn); }
.bdg.bad { background: var(--bad); }
.bdg.ok { background: var(--ok); }
@media (max-width: 640px) {
  .rt { margin-left: -12px; margin-right: -12px; }
  .tab { padding: 0 10px; }
  .tab.on { padding: 0 12px 2px; }
}
</style>
