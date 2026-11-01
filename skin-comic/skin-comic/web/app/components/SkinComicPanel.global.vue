<script setup lang="ts">
/**
 * Panel as a comic panel: thick ink border with a hard shadow, tilted a little (±1.2°, from a hash of the title;
 * only the frame tilts, the content stays straight so text is crisp and overlays inside still cover the screen),
 * title in a yellow caption box in the corner. Tap the caption row to fold (same remembered state as the stock Panel).
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
const rot = computed(() => {
  let h = 7
  for (const c of props.title ?? '') h = (h * 33 + c.charCodeAt(0)) >>> 0
  return `${((h % 25) - 12) / 10}deg`
})
</script>

<template>
  <section :id="id" class="cpanel panel" :class="{ folded: !open }" :style="{ '--rot': rot }">
    <header class="hd" @click="toggle">
      <h2 class="cap">{{ title }}</h2>
      <span v-if="sub" class="sub">{{ sub }}</span>
      <div v-if="open" class="actions" @click.stop><slot name="actions" /></div>
      <button type="button" class="fold" :aria-label="open ? $t('skinComic.fold') : $t('skinComic.unfold')" :aria-expanded="open" @click.stop="toggle"><Icon name="arrow" :size="15" /></button>
    </header>
    <Transition name="cbody">
      <div v-if="open" class="body"><slot /></div>
    </Transition>
  </section>
</template>

<style scoped>
.cpanel { position: relative; z-index: 0; min-width: 0; padding: 0 16px 18px; margin: 4px 4px 8px 0; scroll-margin-top: 16px; }
.cpanel::before {
  content: ''; position: absolute; inset: 0; z-index: -1; pointer-events: none;
  background: var(--panel); border: 3px solid var(--line-2); box-shadow: 5px 5px 0 var(--line-2);
  transform: rotate(var(--rot)); transition: transform .3s cubic-bezier(.3, 1.6, .5, 1);
}
.cpanel:hover::before { transform: rotate(0deg); }
.folded { align-self: start; padding-bottom: 12px; }
.hd { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 0 0 0 -16px; padding-right: 0; cursor: pointer; user-select: none; -webkit-tap-highlight-color: transparent; }
.cap {
  margin: 0; padding: 7px 14px 6px; font-size: 14px; font-weight: 900; font-style: italic; text-transform: uppercase; letter-spacing: .03em; color: var(--line-2);
  background: var(--comic-yellow); border: 3px solid var(--line-2); border-width: 3px 3px 3px 3px; transform: rotate(var(--rot)) translate(-2px, -3px);
}
.sub { font-size: 12.5px; font-weight: 600; color: var(--muted); min-width: 0; padding-top: 4px; }
.actions { margin-left: auto; display: flex; gap: 6px; flex-wrap: wrap; padding-top: 8px; cursor: default; }
.fold {
  margin: 8px 0 0 auto; display: grid; place-items: center; width: 30px; height: 30px; padding: 0; color: var(--line-2); cursor: pointer;
  background: var(--panel); border: 2.5px solid var(--line-2); border-radius: 50%; box-shadow: 2px 2px 0 var(--line-2);
  transform: rotate(90deg); transition: transform .25s cubic-bezier(.3, 1.6, .5, 1);
}
.actions + .fold { margin-left: 0; }
.folded .fold { transform: rotate(0deg); }
.fold:active { box-shadow: none; }
.body { margin-top: 14px; }
.cbody-enter-active { transition: transform .28s cubic-bezier(.3, 1.6, .5, 1), opacity .12s; transform-origin: top left; }
.cbody-leave-active { transition: opacity .1s; }
.cbody-enter-from { transform: scale(.94) rotate(-1deg); opacity: 0; }
.cbody-leave-to { opacity: 0; }
@media (max-width: 640px) { .cpanel { padding: 0 13px 15px; margin-right: 6px; } .hd { margin-left: -13px; } }
@media (pointer: coarse) { .fold { width: 34px; height: 34px; } }
@media (prefers-reduced-motion: reduce) { .cpanel::before, .fold, .cbody-enter-active { transition: none; } }
</style>
