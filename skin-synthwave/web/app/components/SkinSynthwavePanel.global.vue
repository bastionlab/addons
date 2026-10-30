<script setup lang="ts">
/** Panel as a dark glass slab with a neon edge (magenta outside, cyan inside); a scanline sheen sweeps across on
 *  mount and on hover / focus; the header folds it like the stock Panel (same remembered state) */
const props = withDefaults(defineProps<{ title?: string, sub?: string, id?: string, fold?: 'open' | 'closed' | 'phone' }>(), { title: '', fold: 'open' })
const key = props.id ? `panel:${props.id}` : `panel:${useRoute().path}:${props.title}`
const phone = typeof window !== 'undefined' && window.matchMedia('(max-width: 640px)').matches
const open = ref(props.fold === 'open' || (props.fold === 'phone' && !phone))
try { const v = localStorage.getItem(key); if (v) open.value = v === '1' } catch {}
function toggle() {
  open.value = !open.value
  try { localStorage.setItem(key, open.value ? '1' : '0') } catch {}
}
// re-mounting the sheen element restarts its sweep; at most one sweep at a time
const sheen = ref(0)
let busy = false
function sweep() {
  if (busy) return
  busy = true; sheen.value++
  setTimeout(() => (busy = false), 1100)
}
</script>

<template>
  <section :id="id" class="slab panel" :class="{ folded: !open }" @mouseenter="sweep" @focusin="sweep">
    <span class="fx" aria-hidden="true"><i :key="sheen" class="sheen" /></span>
    <header class="hd" @click="toggle">
      <h2>{{ title }}</h2>
      <span v-if="sub" class="sub">{{ sub }}</span>
      <div v-if="open" class="actions" @click.stop><slot name="actions" /></div>
      <button type="button" class="ctl" :aria-expanded="open" :aria-label="open ? $t('skinSynthwave.fold') : $t('skinSynthwave.unfold')" @click.stop="toggle">
        <Icon name="arrow" :size="15" :class="{ open }" />
      </button>
    </header>
    <div v-if="open" class="body"><slot /></div>
  </section>
</template>

<style scoped>
.slab {
  position: relative; min-width: 0; padding: 14px 16px 16px; scroll-margin-top: 70px; border-radius: var(--radius);
  background: linear-gradient(180deg, color-mix(in srgb, var(--panel-2) 88%, transparent), color-mix(in srgb, var(--panel) 92%, transparent));
  border: 1px solid color-mix(in srgb, var(--accent) 60%, transparent);
  box-shadow: 0 0 14px color-mix(in srgb, var(--accent) 30%, transparent), inset 0 0 0 1px rgba(52, 230, 255, .14), inset 0 0 22px rgba(52, 230, 255, .06);
}
.folded { align-self: start; padding-bottom: 12px; }
.fx { position: absolute; inset: 0; border-radius: inherit; overflow: hidden; pointer-events: none; }
.sheen {
  position: absolute; top: 0; bottom: 0; left: 0; width: 45%;
  background: linear-gradient(100deg, transparent, rgba(52, 230, 255, .1) 40%, rgba(255, 255, 255, .16) 50%, rgba(255, 79, 216, .1) 60%, transparent),
    repeating-linear-gradient(0deg, rgba(255, 255, 255, .05) 0 1px, transparent 1px 3px);
  transform: translateX(-110%) skewX(-12deg); animation: sw-sheen .95s ease-out 1;
}
@keyframes sw-sheen { to { transform: translateX(330%) skewX(-12deg); } }
.hd { position: relative; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; min-height: 30px; cursor: pointer; user-select: none; }
h2 { margin: 0; font: italic 700 15px/1.2 "Trebuchet MS", "Futura", system-ui, sans-serif; letter-spacing: .06em; text-transform: uppercase; color: rgb(150 244 255); text-shadow: 0 0 8px rgba(52, 230, 255, .6); }
.sub { font-size: 12px; color: var(--faint); min-width: 0; }
.actions { margin-left: auto; display: flex; gap: 6px; flex-wrap: wrap; cursor: default; }
.ctl { margin-left: auto; width: 32px; height: 30px; display: grid; place-items: center; padding: 0; border-radius: 8px; border: 1px solid color-mix(in srgb, var(--accent) 45%, transparent); background: rgba(0, 0, 0, .25); color: var(--accent); cursor: pointer; }
.actions + .ctl { margin-left: 0; }
.ctl :deep(svg) { transition: transform .2s; }
.ctl :deep(svg.open) { transform: rotate(90deg); }
.body { position: relative; margin-top: 12px; animation: sw-in .25s ease-out; }
@keyframes sw-in { from { opacity: 0; transform: translateY(-4px); } }
@media (max-width: 640px) { .slab { padding: 12px 12px 14px; } }
@media (pointer: coarse) { .ctl { width: 36px; height: 34px; } }
@media (prefers-reduced-motion: reduce) { .sheen { display: none; } .body { animation: none; } .ctl :deep(svg) { transition: none; } }
</style>
