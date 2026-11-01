<script setup lang="ts">
/** Panel as a stone GUI window: stone texture, light/dark block bevels with a black outline, uppercase pixel title; tap the title bar to fold (same remembered state as the stock Panel) */
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
  <section :id="id" class="bpanel panel" :class="{ folded: !open }">
    <header class="hd" @click="toggle">
      <h2 class="ttl">{{ title }}</h2>
      <span v-if="sub" class="sub">{{ sub }}</span>
      <div v-if="open" class="actions" @click.stop><slot name="actions" /></div>
      <button type="button" class="fold" :aria-label="open ? $t('skinBlocky.fold') : $t('skinBlocky.unfold')" :aria-expanded="open" @click.stop="toggle">{{ open ? '-' : '+' }}</button>
    </header>
    <div v-if="open" class="body"><slot /></div>
  </section>
</template>

<style scoped>
.bpanel {
  position: relative; min-width: 0; padding: 10px 14px 14px; scroll-margin-top: 16px; color: var(--text);
  background:
    linear-gradient(90deg, rgba(255, 255, 255, .04) 50%, rgba(0, 0, 0, .04) 0) 0 0 / 8px 8px,
    linear-gradient(0deg, rgba(255, 255, 255, .03) 50%, rgba(0, 0, 0, .05) 0) 0 0 / 12px 12px,
    var(--panel);
  border: 2px solid rgba(0, 0, 0, 1);
  box-shadow: inset 3px 3px 0 rgba(255, 255, 255, .32), inset -3px -3px 0 rgba(0, 0, 0, .38), 4px 4px 0 rgba(0, 0, 0, .3);
}
.folded { align-self: start; padding-bottom: 10px; }
.hd { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; min-height: 32px; cursor: pointer; user-select: none; -webkit-tap-highlight-color: transparent; }
.ttl { margin: 0; font-family: "Courier New", Courier, monospace; font-size: 15px; font-weight: 900; text-transform: uppercase; letter-spacing: .05em; color: var(--text); text-shadow: 2px 2px 0 rgba(40, 40, 40, 1); }
.sub { font-size: 12.5px; color: var(--muted); min-width: 0; }
.actions { margin-left: auto; display: flex; gap: 6px; flex-wrap: wrap; cursor: default; }
.fold {
  margin-left: auto; display: grid; place-items: center; width: 30px; height: 30px; padding: 0; font: inherit; font-size: 18px; font-weight: 900; color: var(--text); cursor: pointer;
  background: rgba(122, 122, 122, 1); border: 2px solid rgba(0, 0, 0, 1); text-shadow: 2px 2px 0 rgba(58, 58, 58, 1);
  box-shadow: inset 2px 2px 0 rgba(170, 170, 170, 1), inset -2px -3px 0 rgba(74, 74, 74, 1);
}
.fold:active { transform: scale(1.06, .85); }
.actions + .fold { margin-left: 0; }
.body { margin-top: 10px; }
@media (max-width: 640px) { .bpanel { padding: 9px 11px 12px; } }
@media (pointer: coarse) { .fold { width: 34px; height: 34px; } }
</style>
