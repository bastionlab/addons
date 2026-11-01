<script setup lang="ts">
/** Panel as a rounded bubble card with a strip of washi tape on top and ✿ before the title; folds with a bounce (same remembered state as the stock Panel) */
const props = withDefaults(defineProps<{ title?: string, sub?: string, id?: string, fold?: 'open' | 'closed' | 'phone' }>(), { title: '', fold: 'open' })
const key = props.id ? `panel:${props.id}` : `panel:${useRoute().path}:${props.title}`
const phone = typeof window !== 'undefined' && window.matchMedia('(max-width: 640px)').matches
const open = ref(props.fold === 'open' || (props.fold === 'phone' && !phone))
try { const v = localStorage.getItem(key); if (v) open.value = v === '1' } catch {}
function toggle() {
  open.value = !open.value
  try { localStorage.setItem(key, open.value ? '1' : '0') } catch {}
}
// each card gets its own tape: a stable pick from the title
const tape = computed(() => [...(props.title || 'x')].reduce((s, c) => s + c.charCodeAt(0), 0) % 4)
</script>

<template>
  <section :id="id" class="bubble panel" :class="[{ folded: !open }, `t${tape}`]">
    <span class="tape" aria-hidden="true" />
    <header class="hd" @click="toggle">
      <h2><span class="fl">{{ '✿' }}</span>{{ title }}</h2>
      <span v-if="sub" class="sub">{{ sub }}</span>
      <div v-if="open" class="actions" @click.stop><slot name="actions" /></div>
      <button type="button" class="tg" :aria-label="open ? $t('skinKawaii.fold') : $t('skinKawaii.unfold')" @click.stop="toggle">
        <Icon name="arrow" :size="15" class="chev" />
      </button>
    </header>
    <Transition name="kw-fold"><div v-if="open" class="body"><slot /></div></Transition>
  </section>
</template>

<style scoped>
.bubble {
  position: relative; min-width: 0; scroll-margin-top: 20px; margin-top: 8px; padding: 16px 18px 18px; border-radius: 24px;
  background: var(--panel); border: 2px solid color-mix(in srgb, var(--accent) 16%, var(--line));
  box-shadow: 0 4px 0 color-mix(in srgb, var(--accent) 12%, var(--line)), 0 12px 26px rgba(214, 69, 140, .1);
}
.folded { align-self: start; padding-bottom: 14px; }
.tape {
  position: absolute; top: -11px; left: 26px; width: 92px; height: 22px; opacity: .85; pointer-events: none; transform: rotate(-4deg);
  border-radius: 2px; box-shadow: 0 1px 2px rgba(122, 84, 105, .15);
  background: repeating-linear-gradient(45deg, rgba(255, 170, 205, .85) 0 6px, rgba(255, 228, 240, .85) 6px 12px);
  clip-path: polygon(3% 0, 97% 0, 100% 20%, 97% 45%, 100% 70%, 97% 100%, 3% 100%, 0 75%, 3% 50%, 0 25%);
}
.t1 .tape { left: auto; right: 30px; transform: rotate(3deg); background: repeating-linear-gradient(-45deg, rgba(170, 214, 255, .85) 0 6px, rgba(232, 244, 255, .85) 6px 12px); }
.t2 .tape { left: 40%; transform: rotate(-2deg); background: repeating-linear-gradient(90deg, rgba(255, 223, 140, .85) 0 7px, rgba(255, 247, 214, .85) 7px 14px); }
.t3 .tape { background: repeating-linear-gradient(45deg, rgba(200, 176, 255, .85) 0 5px, rgba(244, 236, 255, .85) 5px 10px); transform: rotate(5deg); }
.hd { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; min-height: 30px; margin-bottom: 12px; cursor: pointer; user-select: none; }
.folded .hd { margin-bottom: 0; }
h2 { display: flex; align-items: center; gap: 6px; margin: 0; font-size: 15px; font-weight: 800; color: var(--text); }
.fl { color: var(--accent); font-size: 16px; }
.sub { font-size: 12.5px; color: var(--faint); font-weight: 700; min-width: 0; }
.actions { margin-left: auto; display: flex; gap: 6px; flex-wrap: wrap; cursor: default; }
.tg { margin-left: auto; flex: none; display: grid; place-items: center; width: 32px; height: 32px; border-radius: 50%; color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, var(--panel)); border: 0; cursor: pointer; }
.actions + .tg { margin-left: 0; }
.chev { transform: rotate(90deg); transition: transform .35s cubic-bezier(.34, 1.56, .64, 1); }
.folded .chev { transform: rotate(0deg); }
.kw-fold-enter-active { animation: kwfold .5s cubic-bezier(.34, 1.56, .64, 1); transform-origin: top center; }
.kw-fold-leave-active { transition: opacity .15s, transform .15s; transform-origin: top center; }
.kw-fold-leave-to { opacity: 0; transform: scaleY(.85); }
@keyframes kwfold { 0% { opacity: 0; transform: scale(.94, .7); } 60% { opacity: 1; transform: scale(1.01, 1.04); } 100% { transform: none; } }
@media (max-width: 640px) { .bubble { padding: 14px 14px 16px; border-radius: 22px; } }
@media (prefers-reduced-motion: reduce) { .kw-fold-enter-active { animation: none; } .kw-fold-leave-active, .chev { transition: none; } }
</style>
