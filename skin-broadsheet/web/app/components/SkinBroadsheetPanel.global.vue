<script setup lang="ts">
/**
 * Panel as a newspaper article: a drop-cap headline (the title), a small-caps byline (the `sub`), a thin rule,
 * then the story. Folding works like the paper: a folded article ends in "Continued on page B7…" (tap to read on).
 * Same remembered fold state as the stock Panel.
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
const first = computed(() => Array.from(props.title ?? '')[0] ?? '')
const rest = computed(() => Array.from(props.title ?? '').slice(1).join(''))
const page = computed(() => {
  let h = 7
  for (const c of key) h = (h * 33 + c.charCodeAt(0)) % 10007
  return `${String.fromCharCode(66 + (h % 5))}${(h % 19) + 2}`
})
</script>

<template>
  <article :id="id" class="bpanel panel" :class="{ folded: !open }">
    <header class="hd" @click="toggle">
      <span v-if="first" class="dc" aria-hidden="true">{{ first }}</span>
      <div class="hx">
        <h2 :aria-label="title"><span aria-hidden="true">{{ rest }}</span></h2>
        <p class="by">
          <span v-if="sub" class="sub">{{ sub }}</span>
          <button type="button" class="fb" :aria-expanded="open" @click.stop="toggle">{{ open ? $t('skinBroadsheet.fold') : $t('skinBroadsheet.unfold') }}</button>
        </p>
      </div>
      <div v-if="open" class="actions" @click.stop><slot name="actions" /></div>
    </header>
    <hr class="rule">
    <div v-if="open" class="body"><slot /></div>
    <button v-else type="button" class="cont" @click="toggle">{{ $t('skinBroadsheet.continued', { n: page }) }}</button>
  </article>
</template>

<style scoped>
.bpanel {
  position: relative; min-width: 0; padding: 12px 14px 16px; border: 0; border-top: 2px solid var(--text); border-radius: 0;
  background: var(--bs-grain), var(--panel); color: var(--text); font-family: var(--bs-serif); scroll-margin-top: 60px;
}
.folded { align-self: start; padding-bottom: 10px; }
.hd { display: flex; align-items: flex-start; gap: 4px 0; flex-wrap: wrap; cursor: pointer; user-select: none; -webkit-tap-highlight-color: transparent; }
.dc {
  flex: none; font-family: var(--bs-disp); font-weight: 900; font-size: 50px; line-height: .82; color: var(--accent);
  padding: 3px 3px 0 0; text-shadow: 1px 1px 0 rgba(28, 24, 19, .15);
}
.hx { flex: 1 1 160px; min-width: 0; }
h2 { margin: 2px 0 0; font-family: var(--bs-disp); font-weight: 800; font-size: 22px; line-height: 1.1; letter-spacing: 0; color: var(--text); }
.hd:hover h2 { text-decoration: underline; text-decoration-thickness: 1px; text-underline-offset: 3px; }
.by { display: flex; align-items: center; flex-wrap: wrap; gap: 2px 10px; margin: 4px 0 0; font-size: 12.5px; color: var(--muted); }
.sub { font-variant: small-caps; text-transform: lowercase; letter-spacing: .07em; min-width: 0; }
.fb {
  margin-left: auto; min-height: 28px; padding: 0 2px; background: none; border: 0; color: var(--faint); font: inherit; font-style: italic; font-size: 12px; cursor: pointer;
}
.fb:hover { color: var(--accent); text-decoration: underline; }
.actions { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-left: auto; padding-left: 8px; cursor: default; }
.rule { height: 0; margin: 8px 0 12px; border: 0; border-top: 1px solid var(--line-2); }
.body { min-width: 0; line-height: 1.5; }
.cont {
  display: block; margin: -4px 0 0 auto; min-height: 32px; padding: 0; background: none; border: 0; color: var(--accent);
  font: inherit; font-style: italic; font-size: 13.5px; cursor: pointer;
}
.cont:hover { text-decoration: underline; }
@media (max-width: 640px) {
  .bpanel { padding: 10px 12px 14px; }
  .dc { font-size: 44px; }
  h2 { font-size: 20px; }
}
@media (pointer: coarse) { .fb { min-height: 32px; } }
</style>
