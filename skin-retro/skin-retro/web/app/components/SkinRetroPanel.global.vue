<script setup lang="ts">
/** Panel as a window: blue title bar (tap = minimise / restore, same remembered state as the stock Panel), grey body */
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
  <section :id="id" class="win panel" :class="{ folded: !open }">
    <header class="bar" @click="toggle">
      <h2>{{ title }}</h2>
      <span v-if="sub" class="sub">{{ sub }}</span>
      <div v-if="open" class="actions" @click.stop><slot name="actions" /></div>
      <button type="button" class="ctl" :aria-label="open ? $t('skinRetro.fold') : $t('skinRetro.unfold')" @click.stop="toggle">
        <svg v-if="open" viewBox="0 0 10 10" width="10" height="10" aria-hidden="true"><path d="M1 8.5h6" stroke="currentColor" stroke-width="2" /></svg>
        <svg v-else viewBox="0 0 10 10" width="10" height="10" aria-hidden="true"><rect x="1" y="1" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1" /><path d="M1 2h8" stroke="currentColor" stroke-width="2" /></svg>
      </button>
    </header>
    <div v-if="open" class="body"><slot /></div>
  </section>
</template>

<style scoped>
.win { background: var(--panel); border: 2px solid; border-color: var(--line-2) var(--text) var(--text) var(--line-2); box-shadow: inset -1px -1px 0 var(--line), inset 1px 1px 0 var(--panel-2); padding: 3px; min-width: 0; scroll-margin-top: 16px; }
.folded { align-self: start; }
.bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; min-height: 26px; padding: 2px 3px 2px 6px; background: linear-gradient(90deg, var(--accent), color-mix(in srgb, var(--accent) 45%, var(--panel-2))); color: var(--line-2); cursor: pointer; user-select: none; }
h2 { font-size: 13px; font-weight: 700; margin: 0; color: var(--line-2); }
.sub { font-size: 11.5px; color: color-mix(in srgb, var(--line-2) 80%, transparent); min-width: 0; }
.actions { margin-left: auto; display: flex; gap: 4px; flex-wrap: wrap; cursor: default; }
.ctl { margin-left: auto; display: grid; place-items: center; width: 22px; height: 20px; padding: 0; font: 700 12px/1 Tahoma, sans-serif; background: var(--panel); color: var(--text); border: 2px solid; border-color: var(--line-2) var(--text) var(--text) var(--line-2); cursor: pointer; }
.actions + .ctl { margin-left: 0; }
.body { padding: 12px 10px 10px; }
@media (pointer: coarse) { .ctl { width: 34px; height: 30px; } }
</style>
