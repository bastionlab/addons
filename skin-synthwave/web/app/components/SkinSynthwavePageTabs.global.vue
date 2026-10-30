<script setup lang="ts">
/** the page's section tabs as a small neon sign: each tab a neon tube (pink / cyan / sun), the open one lit and flickering on; same behaviour as PageTabs.vue */
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
  <div class="sw-ptabs-wrap">
    <div ref="anchor" />
    <nav class="sw-ptabs" :class="{ l: edge.l, r: edge.r }">
      <div ref="strip" class="strip" role="tablist" @scroll.passive="measure">
        <button
          v-for="(t, i) in tabs" :key="t.key" type="button" role="tab" class="tube" :class="[{ on: model === t.key }, 'h' + (i % 3)]"
          :aria-selected="model === t.key" @click="pick(t.key)"
        >
          <Icon v-if="t.icon" :name="t.icon" :size="15" class="ic" />
          <span>{{ t.label }}</span>
          <span v-if="t.badge" class="bdg" :class="t.tone ?? 'warn'">{{ t.badge }}</span>
        </button>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.sw-ptabs-wrap { display: contents; }
/* a smaller neon sign under the big one: dark glass, magenta rule with glow, every tab a neon tube */
.sw-ptabs {
  --pink: var(--accent); --cyan: rgb(52 230 255); --sun: rgb(255 204 77);
  position: sticky; top: var(--ptabs-top, env(safe-area-inset-top, 0px)); z-index: 20; margin: 0 0 18px;
  border-radius: var(--radius); border: 1px solid color-mix(in srgb, var(--pink) 55%, transparent);
  background: linear-gradient(180deg, rgba(18, 6, 36, .9), rgba(8, 3, 20, .92)); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  box-shadow: 0 0 14px color-mix(in srgb, var(--pink) 30%, transparent), inset 0 0 0 1px rgba(52, 230, 255, .12);
}
.h0 { --glow: var(--pink); } .h1 { --glow: var(--cyan); } .h2 { --glow: var(--sun); }
.strip { display: flex; gap: 4px; overflow-x: auto; scrollbar-width: none; padding: 5px; overscroll-behavior-x: contain; }
.strip::-webkit-scrollbar { display: none; }
.sw-ptabs.l .strip { mask-image: linear-gradient(to right, transparent, black 28px); }
.sw-ptabs.r .strip { mask-image: linear-gradient(to left, transparent, black 28px); }
.sw-ptabs.l.r .strip { mask-image: linear-gradient(to right, transparent, black 28px, black calc(100% - 28px), transparent); }
.tube {
  position: relative; flex: none; display: inline-flex; align-items: center; gap: 6px; min-height: 36px; padding: 4px 13px;
  border-radius: 18px; border: 1px solid transparent; background: none; cursor: pointer; white-space: nowrap;
  font: 600 14px/1 "Arial Rounded MT Bold", "Varela Round", "Trebuchet MS", system-ui, sans-serif; letter-spacing: .03em;
  color: color-mix(in srgb, var(--glow) 45%, var(--muted)); text-shadow: 0 0 2px color-mix(in srgb, var(--glow) 30%, transparent);
  transition: color .2s;
}
.tube:hover, .tube:focus-visible { color: color-mix(in srgb, var(--glow) 75%, var(--text)); outline: none; }
.tube:focus-visible { border-color: color-mix(in srgb, var(--glow) 40%, transparent); }
.tube.on {
  color: var(--text); border-color: color-mix(in srgb, var(--glow) 70%, transparent);
  text-shadow: 0 0 3px var(--glow), 0 0 10px var(--glow), 0 0 22px var(--glow);
  box-shadow: 0 0 10px color-mix(in srgb, var(--glow) 45%, transparent), inset 0 0 10px color-mix(in srgb, var(--glow) 30%, transparent);
  animation: sw-ptab-flicker .7s linear 1;
}
.tube.on .ic { color: var(--glow); filter: drop-shadow(0 0 4px var(--glow)); }
@keyframes sw-ptab-flicker { 0%, 12%, 22%, 36% { opacity: .3; } 8%, 18%, 30%, 44%, 100% { opacity: 1; } }
.bdg { min-width: 18px; padding: 0 5px; border-radius: 9px; font: 700 11px/17px system-ui, sans-serif; text-align: center; text-shadow: none; color: var(--bg); background: var(--warn); box-shadow: 0 0 8px var(--warn); }
.bdg.bad { background: var(--bad); box-shadow: 0 0 8px var(--bad); }
.bdg.ok { background: var(--ok); box-shadow: 0 0 8px var(--ok); }
@media (max-width: 640px) {
  .sw-ptabs { margin: 0 -6px 14px; }
  .tube { min-height: 40px; padding: 4px 12px; font-size: 13.5px; }
}
@media (prefers-reduced-motion: reduce) { .tube.on { animation: none; } .tube { transition: none; } }
</style>

<style>
/* only while this skin is on: on desktop the neon sign is fixed along the top, so the tabs stick under it */
@media (min-width: 641px) { html.skin-synthwave { --ptabs-top: 62px; } }
</style>
