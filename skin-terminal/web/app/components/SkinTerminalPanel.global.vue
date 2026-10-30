<script setup lang="ts">
/**
 * A box-drawn panel: ┌─┤ title ├──── [actions] [-] ─┐. The header sits on the top border (its pieces have the
 * panel's background, so they cut the line like text drawn over a box), [-]/[+] folds it with the same
 * remembered state as the stock Panel.
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
  <section :id="id" class="tpanel panel" :class="{ folded: !open }">
    <header class="hd" @click="toggle">
      <h2><span class="br">{{ '┤' }}</span>{{ title }}<span class="br">{{ '├' }}</span></h2>
      <span v-if="sub" class="sub">{{ sub }}</span>
      <span class="fill" />
      <div v-if="open" class="actions" @click.stop><slot name="actions" /></div>
      <button type="button" class="fold" :aria-label="open ? $t('skinTerminal.fold') : $t('skinTerminal.unfold')" :aria-expanded="open" @click.stop="toggle">{{ open ? '[-]' : '[+]' }}</button>
    </header>
    <div v-if="open" class="body"><slot /></div>
    <p v-else class="dots" aria-hidden="true">{{ '…' }}</p>
  </section>
</template>

<style scoped>
.tpanel {
  position: relative; min-width: 0; margin-top: 14px; padding: 0 16px 16px; border: 1px solid var(--line-2); border-radius: 0;
  background: var(--panel); font-family: var(--tm-mono); scroll-margin-top: 64px;
  box-shadow: inset 0 0 24px rgba(57, 255, 106, .035), 0 0 0 1px rgba(0, 0, 0, .5);
}
/* corner ticks, drawn like box-drawing joints */
.tpanel::before, .tpanel::after { content: ''; position: absolute; width: 7px; height: 7px; border: 0 solid var(--accent); pointer-events: none; }
.tpanel::before { left: -1px; bottom: -1px; border-left-width: 1px; border-bottom-width: 1px; }
.tpanel::after { right: -1px; bottom: -1px; border-right-width: 1px; border-bottom-width: 1px; }
.folded { align-self: start; padding-bottom: 0; }
.hd {
  display: flex; align-items: flex-start; gap: 8px; flex-wrap: wrap; margin: -14px -6px 10px; min-height: 28px;
  cursor: pointer; user-select: none; -webkit-tap-highlight-color: transparent;
}
.folded .hd { margin-bottom: 0; }
h2 {
  display: flex; align-items: center; margin: 0; min-height: 28px; padding: 0 2px; background: var(--panel);
  font-family: var(--tm-mono); font-size: 14px; font-weight: 700; letter-spacing: 0; color: var(--accent);
  text-shadow: 0 0 8px color-mix(in srgb, var(--accent) 45%, transparent);
}
.br { color: var(--line-2); font-weight: 400; padding: 0 5px; text-shadow: none; }
.hd:hover h2 { color: var(--text); }
.sub { display: flex; align-items: center; min-height: 28px; padding: 0 6px; background: var(--panel); font-size: 12px; color: var(--faint); min-width: 0; }
.fill { flex: 1; }
.actions { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; min-height: 28px; padding: 0 4px; background: var(--panel); cursor: default; }
.fold {
  min-width: 34px; height: 28px; padding: 0 4px; background: var(--panel); border: 0; color: var(--muted); font: inherit; font-weight: 700; cursor: pointer;
}
.fold:hover { color: var(--bg); background: var(--accent); }
.body { min-width: 0; }
.dots { margin: -6px 0 2px; color: var(--faint); font-size: 12px; }
@media (max-width: 640px) { .tpanel { padding: 0 12px 14px; } }
@media (pointer: coarse) { .fold { height: 32px; min-width: 40px; } .hd { margin-top: -16px; } .tpanel { margin-top: 16px; } }
</style>
