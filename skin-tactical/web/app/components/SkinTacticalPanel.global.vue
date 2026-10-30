<script setup lang="ts">
/** Panel as a briefing card: one clipped corner, an amber edge, condensed uppercase title, quick fold. */
const props = withDefaults(defineProps<{ title?: string, sub?: string, id?: string, fold?: 'open' | 'closed' | 'phone' }>(), { title: '', fold: 'open' })
const key = props.id ? `panel:${props.id}` : `panel:${useRoute().path}:${props.title}`
const oldKey = `panel:${props.id ?? props.title}`
const phone = typeof window !== 'undefined' && window.matchMedia('(max-width: 640px)').matches
const open = ref(props.fold === 'open' || (props.fold === 'phone' && !phone))
try { const v = localStorage.getItem(key) ?? localStorage.getItem(oldKey); if (v) open.value = v === '1' } catch {}
function toggle() {
  open.value = !open.value
  try { localStorage.setItem(key, open.value ? '1' : '0') } catch {}
}
</script>

<template>
  <section :id="id" class="brief panel" :class="{ folded: !open }">
    <header class="hd" @click="toggle">
      <h2>{{ title }}</h2>
      <span v-if="sub" class="sub">{{ sub }}</span>
      <div v-if="open" class="actions" @click.stop><slot name="actions" /></div>
      <button type="button" class="ctl" :aria-expanded="open" :aria-label="open ? $t('skinTactical.fold') : $t('skinTactical.unfold')" @click.stop="toggle">
        <Icon name="arrow" :size="14" :class="{ down: open }" />
      </button>
    </header>
    <div v-if="open" class="body"><slot /></div>
  </section>
</template>

<style scoped>
.brief {
  position: relative; min-width: 0; padding: 12px 16px 16px; scroll-margin-top: 80px;
  background: var(--panel); border: 1px solid var(--line); border-left: 2px solid var(--accent);
  clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 0 100%);
}
.folded { align-self: start; padding-bottom: 12px; }
.hd { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; min-height: 32px; cursor: pointer; user-select: none; }
h2 { margin: 0; font: 700 14px/1.2 "Bahnschrift", "Arial Narrow", "Roboto Condensed", system-ui, sans-serif; text-transform: uppercase; letter-spacing: .1em; color: var(--text); }
.hd:hover h2 { color: var(--accent); }
.sub { font-size: 12px; color: var(--faint); min-width: 0; }
.actions { margin-left: auto; display: flex; gap: 6px; flex-wrap: wrap; cursor: default; }
.ctl { margin-left: auto; width: 32px; height: 30px; display: grid; place-items: center; padding: 0; border: 1px solid var(--line); background: transparent; color: var(--muted); cursor: pointer; }
.actions + .ctl { margin-left: 0; }
.ctl .down { transform: rotate(90deg); }
.body { margin-top: 12px; }
@media (max-width: 640px) { .brief { padding: 12px 12px 14px; } }
</style>
