<script setup lang="ts">
/** Panel as an M3 filled card: 28px corners, title row with the actions and a fold icon button; folding animates the height */
const props = withDefaults(defineProps<{ title?: string, sub?: string, id?: string, fold?: 'open' | 'closed' | 'phone' }>(), { title: '', fold: 'open' })
const key = props.id ? `panel:${props.id}` : `panel:${useRoute().path}:${props.title}`
const phone = typeof window !== 'undefined' && window.matchMedia('(max-width: 640px)').matches
const open = ref(props.fold === 'open' || (props.fold === 'phone' && !phone))
try { const v = localStorage.getItem(key); if (v) open.value = v === '1' } catch {}
function toggle() {
  open.value = !open.value
  try { localStorage.setItem(key, open.value ? '1' : '0') } catch {}
}
const still = () => typeof window === 'undefined' || window.matchMedia('(prefers-reduced-motion: reduce)').matches
function slide(el: Element, done: () => void, show: boolean) {
  const e = el as HTMLElement
  if (still() || !e.animate) return done()
  const h = `${e.scrollHeight}px`
  e.style.overflow = 'hidden'
  const a = e.animate(show ? [{ height: '0px', opacity: 0 }, { height: h, opacity: 1 }] : [{ height: h, opacity: 1 }, { height: '0px', opacity: 0 }],
    { duration: show ? 300 : 200, easing: show ? 'cubic-bezier(.2, 0, 0, 1)' : 'cubic-bezier(.3, 0, .8, .15)' })
  const end = () => { e.style.overflow = ''; done() }
  a.onfinish = end
  a.oncancel = end
}
</script>

<template>
  <section :id="id" class="m3-panel panel" :class="{ folded: !open }">
    <header @click="toggle">
      <h2>{{ title }}</h2>
      <span v-if="sub" class="sub">{{ sub }}</span>
      <div v-if="open" class="actions" @click.stop><slot name="actions" /></div>
      <button type="button" class="fold m3-rip" :aria-expanded="open" :aria-label="open ? $t('skinMaterial.fold') : $t('skinMaterial.unfold')" @click.stop="toggle">
        <Icon name="arrow" :size="20" />
      </button>
    </header>
    <Transition :css="false" @enter="(el, done) => slide(el, done, true)" @leave="(el, done) => slide(el, done, false)">
      <div v-if="open" class="body"><slot /></div>
    </Transition>
  </section>
</template>

<style scoped>
.m3-panel { min-width: 0; padding: 8px 16px 16px; border-radius: 28px; background: var(--panel); scroll-margin-top: 80px; }
.folded { align-self: start; padding-bottom: 8px; }
header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; min-height: 48px; margin: 0 -8px 0 -16px; padding: 0 8px 0 16px; border-radius: 28px; cursor: pointer; user-select: none; -webkit-tap-highlight-color: transparent; }
h2 { margin: 0; font-size: 16px; font-weight: 500; line-height: 24px; letter-spacing: .15px; color: var(--text); }
.sub { min-width: 0; font-size: 12px; letter-spacing: .4px; color: var(--muted); }
.actions { margin-left: auto; display: flex; gap: 6px; flex-wrap: wrap; cursor: default; }
.fold { margin-left: auto; display: grid; place-items: center; width: 40px; height: 40px; flex: none; padding: 0; border: 0; border-radius: 50%; background: none; color: var(--muted); cursor: pointer; }
.actions + .fold { margin-left: 0; }
@media (hover: hover) { .fold:hover { background: color-mix(in srgb, var(--text) 8%, transparent); } }
.fold :deep(svg) { transform: rotate(90deg); transition: transform .3s cubic-bezier(.2, 0, 0, 1); }
.folded .fold :deep(svg) { transform: rotate(0deg); }
.body { padding-top: 8px; }
@media (max-width: 640px) { .m3-panel { padding: 6px 14px 14px; border-radius: 24px; } .folded { padding-bottom: 6px; } }
@media (prefers-reduced-motion: reduce) { .fold :deep(svg) { transition: none; } }
</style>
