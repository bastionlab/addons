<script setup lang="ts">
/**
 * Panel as a lit dance-floor box: a rainbow border that slowly turns (a conic gradient spinning inside a clipped rim,
 * transform only), a dark violet fill, a neon LED + title. Panels bounce in with a stagger when a page loads
 * (order = the order they mount in, reset after a quiet 400 ms). Tap the header to fold (same remembered state
 * as the stock Panel).
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
// stagger: shared across panels on the page via a tiny global counter
const g = globalThis as unknown as { __discoStag?: { at: number, n: number } }
const now = typeof performance !== 'undefined' ? performance.now() : 0
const st = g.__discoStag && now - g.__discoStag.at < 400 ? g.__discoStag : { at: now, n: 0 }
st.at = now
const delay = `${Math.min(st.n++, 10) * 70}ms`
g.__discoStag = st
// each panel's rainbow starts at a different angle so a grid doesn't pulse in lockstep
const turn = computed(() => {
  let h = 5
  for (const c of props.title ?? '') h = (h * 31 + c.charCodeAt(0)) >>> 0
  return `${h % 360}deg`
})
</script>

<template>
  <section :id="id" class="dpanel panel" :class="{ folded: !open }" :style="{ '--d': delay, '--turn': turn }">
    <span class="rim" aria-hidden="true"><i /></span>
    <span class="fill" aria-hidden="true" />
    <header class="hd" @click="toggle">
      <i class="led" aria-hidden="true" />
      <h2 class="ttl">{{ title }}</h2>
      <span v-if="sub" class="sub">{{ sub }}</span>
      <div v-if="open" class="actions" @click.stop><slot name="actions" /></div>
      <button type="button" class="fold" :aria-label="open ? $t('skinDisco.fold') : $t('skinDisco.unfold')" :aria-expanded="open" @click.stop="toggle"><Icon name="arrow" :size="15" /></button>
    </header>
    <Transition name="dbody">
      <div v-if="open" class="body"><slot /></div>
    </Transition>
  </section>
</template>

<style scoped>
.dpanel {
  position: relative; z-index: 0; min-width: 0; padding: 12px 16px 16px; border-radius: var(--radius, 14px); scroll-margin-top: 16px;
  animation: dbounce .6s cubic-bezier(.3, 1.5, .5, 1) var(--d, 0ms) both;
}
.rim { position: absolute; inset: 0; z-index: -2; border-radius: inherit; overflow: hidden; container-type: size; pointer-events: none; }
.rim i {
  position: absolute; left: 50%; top: 50%; width: calc(120cqw + 120cqh); aspect-ratio: 1; margin: calc((60cqw + 60cqh) * -1) 0 0 calc((60cqw + 60cqh) * -1);
  background: conic-gradient(from var(--turn), rgba(255, 63, 180, 1), rgba(255, 201, 63, 1), rgba(63, 242, 160, 1), rgba(63, 216, 255, 1), rgba(180, 75, 255, 1), rgba(255, 63, 180, 1));
  animation: drim 8s linear infinite; will-change: transform;
}
.fill {
  position: absolute; inset: 2px; z-index: -1; border-radius: calc(var(--radius, 14px) - 2px); pointer-events: none;
  background: linear-gradient(180deg, color-mix(in srgb, var(--panel) 94%, transparent), color-mix(in srgb, var(--bg) 94%, transparent));
  box-shadow: inset 0 0 24px rgba(180, 75, 255, .15);
}
@keyframes drim { to { transform: rotate(360deg); } }
@keyframes dbounce {
  0% { opacity: 0; transform: translateY(26px) scale(.96); }
  60% { opacity: 1; transform: translateY(-5px) scale(1.01); }
  100% { opacity: 1; transform: none; }
}
.folded { align-self: start; padding-bottom: 12px; }
.hd { display: flex; align-items: center; gap: 9px; flex-wrap: wrap; min-height: 32px; cursor: pointer; user-select: none; -webkit-tap-highlight-color: transparent; }
.led { flex: none; width: 9px; height: 9px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 8px var(--accent), 0 0 2px var(--text); }
.ttl { margin: 0; font-size: 15px; font-weight: 800; font-style: italic; letter-spacing: .03em; color: var(--text); text-shadow: 0 0 10px rgba(255, 63, 180, .45); }
.sub { font-size: 12.5px; color: var(--muted); min-width: 0; }
.actions { margin-left: auto; display: flex; gap: 6px; flex-wrap: wrap; cursor: default; }
.fold {
  margin-left: auto; display: grid; place-items: center; width: 30px; height: 30px; padding: 0; color: var(--text); cursor: pointer;
  background: rgba(10, 4, 20, .6); border: 1.5px solid var(--line-2); border-radius: 50%;
  transform: rotate(90deg); transition: transform .3s cubic-bezier(.3, 1.6, .5, 1);
}
.actions + .fold { margin-left: 0; }
.folded .fold { transform: rotate(0deg); }
.body { margin-top: 12px; }
.dbody-enter-active { transition: transform .3s cubic-bezier(.3, 1.5, .5, 1), opacity .15s; transform-origin: top; }
.dbody-leave-active { transition: opacity .1s; }
.dbody-enter-from { transform: scaleY(.9) translateY(-6px); opacity: 0; }
.dbody-leave-to { opacity: 0; }
@media (max-width: 640px) { .dpanel { padding: 10px 13px 14px; } }
@media (pointer: coarse) { .fold { width: 34px; height: 34px; } }
@media (max-width: 640px), (pointer: coarse) { .rim i { animation: none; } }
@media (prefers-reduced-motion: reduce) {
  .dpanel, .rim i { animation: none; }
  .fold, .dbody-enter-active { transition: none; }
}
</style>
