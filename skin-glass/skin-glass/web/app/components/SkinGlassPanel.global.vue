<script setup lang="ts">
/**
 * Panel as a sheet of glass: frosted layer (on a pseudo-element, so fixed overlays inside still cover the screen),
 * hairline border, inner highlight and a specular glint that follows the pointer. Tap the header to fold
 * (same remembered state as the stock Panel); the body springs in and out.
 */
const props = withDefaults(defineProps<{ title?: string, sub?: string, id?: string, fold?: 'open' | 'closed' | 'phone' }>(), { title: '', fold: 'open' })
const key = props.id ? `panel:${props.id}` : `panel:${useRoute().path}:${props.title}`
const phone = typeof window !== 'undefined' && window.matchMedia('(max-width: 640px)').matches
const open = ref(props.fold === 'open' || (props.fold === 'phone' && !phone))
try { const v = localStorage.getItem(key); if (v) open.value = v === '1' } catch {}
function toggle() {
  open.value = !open.value
  try { localStorage.setItem(key, open.value ? '1' : '0') } catch {}
}
const el = ref<HTMLElement | null>(null)
function glint(e: PointerEvent) {
  const n = el.value
  if (!n) return
  const r = n.getBoundingClientRect()
  n.style.setProperty('--mx', `${e.clientX - r.left}px`)
  n.style.setProperty('--my', `${e.clientY - r.top}px`)
}
</script>

<template>
  <section :id="id" ref="el" class="gpanel panel" :class="{ folded: !open }" @pointermove="glint" @pointerdown="glint">
    <header class="hd" @click="toggle">
      <h2>{{ title }}</h2>
      <span v-if="sub" class="sub">{{ sub }}</span>
      <div v-if="open" class="actions" @click.stop><slot name="actions" /></div>
      <button type="button" class="chev" :aria-label="open ? $t('skinGlass.fold') : $t('skinGlass.unfold')" :aria-expanded="open" @click.stop="toggle"><Icon name="arrow" :size="14" /></button>
    </header>
    <Transition name="gfold">
      <div v-if="open" class="body"><slot /></div>
    </Transition>
  </section>
</template>

<style scoped>
.gpanel { position: relative; z-index: 0; min-width: 0; padding: 18px 20px 20px; border-radius: 24px; scroll-margin-top: 64px; }
.gpanel::before {
  content: ''; position: absolute; inset: 0; z-index: -1; border-radius: inherit; pointer-events: none;
  background: linear-gradient(165deg, rgba(255, 255, 255, .11), rgba(255, 255, 255, .035) 45%, rgba(255, 255, 255, .06));
  border: 1px solid rgba(255, 255, 255, .13);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .22), inset 0 0 0 1px rgba(255, 255, 255, .02), 0 18px 40px rgba(0, 0, 0, .32);
  backdrop-filter: blur(26px) saturate(170%); -webkit-backdrop-filter: blur(26px) saturate(170%);
}
.gpanel::after {
  content: ''; position: absolute; inset: 0; z-index: -1; border-radius: inherit; pointer-events: none; opacity: 0;
  background: radial-gradient(420px circle at var(--mx, 50%) var(--my, 0%), rgba(255, 255, 255, .11), transparent 45%);
  transition: opacity .35s;
}
.gpanel:hover::after, .gpanel:active::after { opacity: 1; }
.folded { align-self: start; padding-bottom: 18px; }
.hd { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; min-height: 30px; cursor: pointer; user-select: none; -webkit-tap-highlight-color: transparent; }
h2 { margin: 0; font-size: 17px; font-weight: 700; letter-spacing: -.02em; color: var(--text); }
.sub { font-size: 12.5px; color: var(--muted); min-width: 0; }
.actions { margin-left: auto; display: flex; gap: 6px; flex-wrap: wrap; cursor: default; }
.chev {
  margin-left: auto; display: grid; place-items: center; width: 30px; height: 30px; padding: 0; border-radius: 50%; color: var(--muted); cursor: pointer;
  background: rgba(255, 255, 255, .07); border: 1px solid rgba(255, 255, 255, .1);
  transform: rotate(90deg); transition: transform .5s cubic-bezier(.34, 1.56, .64, 1), color .2s;
}
.actions + .chev { margin-left: 0; }
.folded .chev { transform: rotate(0deg); }
.hd:hover .chev { color: var(--text); }
.body { margin-top: 14px; transform-origin: top center; }
.gfold-enter-active { transition: opacity .3s ease, transform .5s cubic-bezier(.34, 1.4, .64, 1); }
.gfold-leave-active { transition: opacity .15s ease, transform .18s ease-in; }
.gfold-enter-from { opacity: 0; transform: translateY(-10px) scale(.97); }
.gfold-leave-to { opacity: 0; transform: translateY(-6px) scale(.98); }
@media (max-width: 640px) {
  .gpanel { padding: 15px 15px 17px; border-radius: 22px; }
  .gpanel::before { backdrop-filter: blur(16px) saturate(160%); -webkit-backdrop-filter: blur(16px) saturate(160%); }
}
@media (pointer: coarse) { .chev { width: 34px; height: 34px; } }
@media (prefers-reduced-motion: reduce) {
  .chev, .gfold-enter-active, .gfold-leave-active { transition: none; }
}
</style>
