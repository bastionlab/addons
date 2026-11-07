<script setup lang="ts">
/**
 * M3 tonal backdrop: the surface with two soft "expressive shapes" in faint tones of the seed colour (a nine-scallop
 * cookie top-right, a tilted pill bottom-left) and a tonal glow from the top. The shapes turn very slowly and, on
 * every page change, glide to that page's own spot, like dynamic colour settling. Paused while hidden, still under
 * reduced motion.
 */
const props = withDefaults(defineProps<{ path?: string }>(), { path: '/' })
const paused = ref(false)
const onVis = () => (paused.value = document.hidden)
onMounted(() => { onVis(); document.addEventListener('visibilitychange', onVis) })
onUnmounted(() => document.removeEventListener('visibilitychange', onVis))

// the cookie: r(θ) = R + A·cos(9θ), sampled into one smooth closed path
const COOKIE = (() => {
  const pts: string[] = []
  for (let i = 0; i < 180; i++) {
    const a = (i / 180) * Math.PI * 2
    const r = 44 + 4.2 * Math.cos(9 * a)
    pts.push(`${(50 + Math.cos(a) * r).toFixed(2)} ${(50 + Math.sin(a) * r).toFixed(2)}`)
  }
  return `M${pts.join('L')}Z`
})()

// a stable spot per page (first path segment), so each page has its own arrangement
const spot = computed(() => {
  let h = 7
  for (const c of props.path.split('/')[1] || 'home') h = (h * 31 + c.charCodeAt(0)) >>> 0
  return {
    '--c-x': `${(h % 9) - 4}vmin`, '--c-y': `${((h >> 4) % 9) - 4}vmin`, '--c-r': `${(h >> 8) % 40}deg`, '--c-s': `${0.92 + ((h >> 3) % 5) * 0.04}`,
    '--p-x': `${((h >> 6) % 11) - 5}vmin`, '--p-y': `${((h >> 10) % 7) - 3}vmin`, '--p-r': `${-24 + ((h >> 5) % 13)}deg`,
  }
})
</script>

<template>
  <div class="m3-bd" :class="{ paused }" :style="spot" aria-hidden="true">
    <div class="glow" />
    <div class="cookie">
      <div class="turn"><svg viewBox="0 0 100 100" width="100%" height="100%"><path :d="COOKIE" /></svg></div>
    </div>
    <div class="pillw"><div class="pill" /></div>
  </div>
</template>

<style scoped>
.m3-bd { position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; background: var(--bg); }
.glow { position: absolute; inset: 0; background: radial-gradient(120% 70% at 70% -10%, color-mix(in srgb, var(--accent) 9%, transparent), transparent 60%); }
.cookie {
  position: absolute; top: -16vmin; right: -14vmin; width: 68vmin; height: 68vmin;
  transform: translate(var(--c-x), var(--c-y)) rotate(var(--c-r)) scale(var(--c-s));
  transition: transform 1.4s cubic-bezier(.2, 0, 0, 1);
}
.turn { width: 100%; height: 100%; will-change: transform; animation: m3-turn 140s linear infinite; }
.turn svg { display: block; }
.turn path { fill: color-mix(in srgb, var(--accent) 8%, var(--bg)); }
.pillw {
  position: absolute; left: -18vmin; bottom: -8vmin; width: 78vmin; height: 30vmin;
  transform: translate(var(--p-x), var(--p-y)) rotate(var(--p-r)); transition: transform 1.6s cubic-bezier(.2, 0, 0, 1);
}
.pill { width: 100%; height: 100%; border-radius: 999px; background: color-mix(in srgb, var(--accent) 6%, var(--bg)); animation: m3-breathe 24s ease-in-out infinite alternate; }
@keyframes m3-turn { to { transform: rotate(360deg); } }
@keyframes m3-breathe { from { transform: scale(1); } to { transform: scale(1.06, .94); } }
.paused .turn, .paused .pill { animation-play-state: paused; }
@media (max-width: 640px) {
  .cookie { top: -10vmin; right: -22vmin; width: 80vmin; height: 80vmin; }
  .pill { animation: none; }
  .pillw { left: -30vmin; bottom: 6vh; width: 96vmin; height: 34vmin; }
}
@media (prefers-reduced-motion: reduce) {
  .turn, .pill { animation: none; }
  .cookie, .pillw { transition: none; }
}
</style>
