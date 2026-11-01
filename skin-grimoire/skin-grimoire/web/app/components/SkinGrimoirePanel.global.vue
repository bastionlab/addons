<script setup lang="ts">
/**
 * Panel as a page of the book: dark parchment inside a double gold rule, the title in gold small caps.
 * Tapping the header folds it (same remembered key as the stock Panel).
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
</script>

<template>
  <section :id="id" class="gm-panel panel" :class="{ folded: !open }">
    <header @click="toggle">
      <button type="button" class="fold" :aria-expanded="open" :aria-label="open ? $t('skinGrimoire.fold') : $t('skinGrimoire.unfold')" @click.stop="toggle"><Icon name="arrow" :size="12" class="chev" /></button>
      <h2>{{ title }}</h2>
      <span v-if="sub" class="sub">{{ sub }}</span>
      <div v-if="open" class="actions" @click.stop><slot name="actions" /></div>
    </header>
    <div v-if="open" class="body"><slot /></div>
  </section>
</template>

<style scoped>
.gm-panel {
  position: relative; min-width: 0; padding: 14px 18px 18px; border-radius: 3px; scroll-margin-top: 16px;
  background: color-mix(in srgb, var(--panel) 96%, transparent);
  border: 1px solid color-mix(in srgb, var(--warn) 30%, transparent);
  outline: 1px solid color-mix(in srgb, var(--warn) 12%, transparent); outline-offset: -5px;
}
.folded { align-self: start; padding-bottom: 12px; }
header { display: flex; align-items: center; gap: 4px 8px; flex-wrap: wrap; min-height: 32px; margin: -4px 0 12px -8px; cursor: pointer; user-select: none; }
.folded header { margin-bottom: -4px; }
h2 { margin: 0; min-width: 0; font: 600 13px/1.3 Georgia, "Palatino Linotype", serif; letter-spacing: .16em; text-transform: uppercase; color: var(--warn); }
.sub { min-width: 0; font-size: 12px; font-style: italic; color: var(--muted); }
.actions { margin-left: auto; display: flex; gap: 6px; flex-wrap: wrap; cursor: default; }
.fold { display: grid; place-items: center; width: 32px; height: 32px; flex: none; padding: 0; border: 0; background: none; color: var(--faint); cursor: pointer; -webkit-tap-highlight-color: transparent; }
.chev { transform: rotate(90deg); transition: transform .2s; }
.folded .chev { transform: none; }
@media (max-width: 640px) { .gm-panel { padding: 12px 14px 16px; } }
@media (prefers-reduced-motion: reduce) { .chev { transition: none; } }
</style>
