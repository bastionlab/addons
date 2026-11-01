<script setup lang="ts">
/**
 * Page tabs as a newspaper's section index: a row of small-caps entries, each with its page letter (A, B, C…),
 * between a double and a single rule; the open one is bold, underlined and its letter inverted. Sticky under the
 * masthead's section index on desktop, sideways scroll on a phone with the open tab kept in view.
 */
defineProps<{ tabs: { key: string, label: string, icon?: string, badge?: number | string, tone?: 'ok' | 'warn' | 'bad' }[] }>()
const model = defineModel<string>({ required: true })
const anchor = ref<HTMLElement>()
const strip = ref<HTMLElement>()
const letter = (i: number) => String.fromCharCode(65 + (i % 26))

function reveal(smooth = true) {
  const s = strip.value
  const b = s?.querySelector<HTMLElement>('.on')
  if (!s || !b) return
  s.scrollTo({ left: Math.max(0, b.offsetLeft - (s.clientWidth - b.offsetWidth) / 2), behavior: smooth ? 'smooth' : 'auto' })
}
function pick(k: string) {
  if (k === model.value) return
  model.value = k
  const a = anchor.value
  const stick = parseFloat(getComputedStyle(a?.nextElementSibling ?? document.body).top) || 0
  const y = a?.getBoundingClientRect().top ?? 0
  if (a && y < stick) window.scrollTo({ top: window.scrollY + y - stick })
}
watch(model, () => nextTick(() => reveal()))
onMounted(() => nextTick(() => reveal(false)))
</script>

<template>
  <div class="bpt-wrap">
    <div ref="anchor" />
    <nav class="bpt">
      <div ref="strip" class="strip" role="tablist">
        <button
          v-for="(t, i) in tabs" :key="t.key" type="button" role="tab" class="pt" :class="{ on: model === t.key }"
          :aria-selected="model === t.key" @click="pick(t.key)"
        >
          <span class="lt">{{ letter(i) }}</span>
          <span class="lb">{{ t.label }}</span>
          <sup v-if="t.badge" class="bdg" :class="t.tone ?? 'warn'">{{ t.badge }}</sup>
        </button>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.bpt-wrap { display: contents; }
.bpt {
  position: sticky; top: var(--ptabs-top, 0px); z-index: 20; margin: 0 0 18px; background: var(--bg);
  border-top: 3px double var(--text); border-bottom: 1px solid var(--text); font-family: var(--bs-serif);
}
.strip { display: flex; overflow-x: auto; scrollbar-width: none; overscroll-behavior-x: contain; }
.strip::-webkit-scrollbar { display: none; }
.pt {
  position: relative; flex: none; display: inline-flex; align-items: center; gap: 7px; min-height: 38px; padding: 0 14px; border: 0; background: none;
  color: var(--text); font: inherit; font-size: 15px; white-space: nowrap; cursor: pointer; -webkit-tap-highlight-color: transparent;
}
.pt + .pt::before { content: ''; position: absolute; left: 0; top: 10px; bottom: 10px; border-left: 1px solid var(--line-2); }
.lt {
  display: inline-grid; place-items: center; width: 20px; height: 20px; border: 1px solid var(--text);
  font-family: var(--bs-disp); font-weight: 800; font-size: 12px; line-height: 1;
}
.lb { font-variant: small-caps; text-transform: lowercase; letter-spacing: .08em; }
.pt:hover .lb { text-decoration: underline; text-underline-offset: 4px; }
.pt.on .lb { font-weight: 800; text-decoration: underline; text-decoration-thickness: 2px; text-underline-offset: 5px; }
.pt.on .lt { background: var(--text); color: var(--bg); }
.bdg { font-size: 11px; font-weight: 800; color: var(--warn); }
.bdg.bad { color: var(--bad); }
.bdg.ok { color: var(--ok); }
@media (max-width: 640px) {
  .bpt { margin-left: -12px; margin-right: -12px; padding: 0 4px; }
  .pt { min-height: 42px; padding: 0 12px; }
}
</style>
