<script setup lang="ts">
/**
 * A page's own sections as Material 3 primary tabs: a surface row with a divider, icon + label per tab, the open tab
 * in the primary colour with a 3 px rounded active indicator under its content that slides from tab to tab.
 * Sticks under the phone's top app bar, scrolls sideways on a phone with the open tab kept in view.
 */
const props = defineProps<{ tabs: { key: string, label: string, icon?: string, badge?: number | string, tone?: 'ok' | 'warn' | 'bad' }[] }>()
const model = defineModel<string>({ required: true })
const { anchor, strip, nav, edge, measure, pick, fit } = usePageTabs({ count: () => props.tabs.length, model, autoCompact: true })
const ind = ref({ x: 0, w: 0, ready: false })

// the indicator sits under the open tab's content (strip coordinates, so it scrolls along with the tabs)
function place() {
  const s = strip.value
  const c = s?.querySelector<HTMLElement>('.on .in')
  if (!s || !c) { ind.value = { ...ind.value, w: 0 }; return }
  const sr = s.getBoundingClientRect()
  const cr = c.getBoundingClientRect()
  ind.value = { x: cr.left - sr.left + s.scrollLeft, w: cr.width, ready: true }
}
// see-through until it reaches its sticky spot, so a page that opens with its tabs doesn't cut a band out of the backdrop
const stuck = ref(false)
let raf = 0
function onScroll() {
  if (raf) return
  raf = requestAnimationFrame(() => {
    raf = 0
    const a = anchor.value
    const n = a?.nextElementSibling
    if (!a || !n) return
    stuck.value = a.getBoundingClientRect().top < (parseFloat(getComputedStyle(n).top) || 0) + 1
  })
}
// usePageTabs refits (and may flip is-compact) on its own resize listener: place the indicator after it
const onResize = () => { fit(); place(); onScroll() }
watch(model, () => nextTick(() => place()))
onMounted(() => {
  nextTick(() => { fit(); place(); onScroll() })
  window.addEventListener('resize', onResize)
  window.addEventListener('scroll', onScroll, { passive: true })
})
onBeforeUnmount(() => { window.removeEventListener('resize', onResize); window.removeEventListener('scroll', onScroll); cancelAnimationFrame(raf) })
watch(() => props.tabs, () => nextTick(onResize), { deep: true })
</script>

<template>
  <div class="m3t-wrap">
    <div ref="anchor" />
    <nav ref="nav" class="m3t" :class="{ l: edge.l, r: edge.r, stuck }">
      <div ref="strip" class="strip" role="tablist" @scroll.passive="measure">
        <button
          v-for="t in tabs" :key="t.key" type="button" role="tab" class="tab m3-rip" :class="{ on: model === t.key, ico: !!t.icon }"
          :aria-selected="model === t.key" :aria-label="t.label" :title="t.label" @click="pick(t.key)"
        >
          <span class="in">
            <Icon v-if="t.icon" :name="t.icon" :size="20" />
            <span class="lab">{{ t.label }}</span>
            <span v-if="t.badge" class="bdg" :class="t.tone ?? 'warn'">{{ t.badge }}</span>
          </span>
        </button>
        <span class="ind" :class="{ ready: ind.ready }" :style="{ transform: `translateX(${ind.x}px)`, width: `${ind.w}px` }" aria-hidden="true" />
      </div>
    </nav>
  </div>
</template>

<style scoped>
.m3t-wrap { display: contents; }
.m3t {
  position: sticky; top: var(--ptabs-top, env(safe-area-inset-top, 0px)); z-index: 20; margin: 0 0 16px;
  background: transparent; border-bottom: 1px solid var(--line); transition: background-color .2s;
}
.m3t.stuck { background: var(--m3-surf, var(--panel)); }
.strip { position: relative; display: flex; overflow-x: auto; scrollbar-width: none; overscroll-behavior-x: contain; }
.strip::-webkit-scrollbar { display: none; }
.m3t.l .strip { mask-image: linear-gradient(to right, transparent, black 28px); }
.m3t.r .strip { mask-image: linear-gradient(to left, transparent, black 28px); }
.m3t.l.r .strip { mask-image: linear-gradient(to right, transparent, black 28px, black calc(100% - 28px), transparent); }
.tab {
  flex: none; display: grid; place-items: center; min-width: 90px; height: 48px; padding: 0 16px; border: 0; border-radius: 0;
  background: none; color: var(--muted); font: inherit; font-size: 14px; font-weight: 500; letter-spacing: .1px; white-space: nowrap;
  cursor: pointer; -webkit-tap-highlight-color: transparent; transition: background-color .15s, color .15s;
}
@media (hover: hover) { .tab:hover { background: color-mix(in srgb, var(--text) 8%, transparent); color: var(--text); } }
.tab:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.tab.on { color: var(--accent); }
@media (hover: hover) { .tab.on:hover { background: color-mix(in srgb, var(--accent) 8%, transparent); color: var(--accent); } }
.in { display: inline-flex; align-items: center; gap: 8px; }
.ind {
  position: absolute; left: 0; bottom: 0; height: 3px; min-width: 24px; border-radius: 3px 3px 0 0; background: var(--accent);
  pointer-events: none; opacity: 0;
}
.ind.ready { opacity: 1; transition: transform .3s cubic-bezier(.2, 0, 0, 1), width .3s cubic-bezier(.2, 0, 0, 1); }
.bdg {
  min-width: 16px; height: 16px; padding: 0 4px; border-radius: 8px; font-size: 11px; font-weight: 500; line-height: 16px; text-align: center;
  background: var(--warn); color: color-mix(in srgb, var(--warn) 18%, black);
}
.bdg.bad { background: var(--bad); color: color-mix(in srgb, var(--bad) 18%, black); }
.bdg.ok { background: var(--ok); color: color-mix(in srgb, var(--ok) 18%, black); }
@media (max-width: 640px) {
  .m3t { margin-left: -12px; margin-right: -12px; }
  .tab { min-width: 0; padding: 0 14px; }
  /* phone, only when the row overflows (is-compact): a closed tab with an icon shows only the icon (its name is in aria-label/title); the open one keeps its label */
  .m3t.is-compact .tab.ico:not(.on) { min-width: 52px; padding: 0 12px; }
  .m3t.is-compact .tab.ico:not(.on) .lab { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  .tab, .ind.ready { transition: none; }
}
</style>

<style>
/* on a phone the top app bar is fixed at the top: the tabs stick right under it */
@media (max-width: 640px) {
  html.skin-material { --ptabs-top: calc(64px + env(safe-area-inset-top, 0px)); }
}
</style>
