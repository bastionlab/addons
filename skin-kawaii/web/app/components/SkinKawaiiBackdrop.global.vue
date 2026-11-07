<script setup lang="ts">
/** pastel sky: a soft gradient, clouds drifting sideways and little hearts / stars / petals floating up */
defineProps<{ path?: string }>()
const paused = ref(false)
const onVis = () => (paused.value = document.hidden)
onMounted(() => { onVis(); document.addEventListener('visibilitychange', onVis) })
onUnmounted(() => document.removeEventListener('visibilitychange', onVis))

const CLOUDS = [
  { top: 8, s: 1.1, d: 95, o: -10 }, { top: 26, s: .7, d: 70, o: -40 },
  { top: 52, s: .9, d: 120, o: -75 }, { top: 74, s: .6, d: 80, o: -20 },
]
// kind, left %, size px, rise seconds, delay, colour
const BITS = [
  { k: 'heart', x: 6, s: 18, d: 22, l: 0, c: '#ff9cc8' }, { k: 'star', x: 15, s: 14, d: 27, l: -9, c: '#ffd36e' },
  { k: 'petal', x: 24, s: 16, d: 25, l: -4, c: '#ffc0dc' }, { k: 'heart', x: 33, s: 12, d: 30, l: -18, c: '#c9a8ff' },
  { k: 'star', x: 42, s: 18, d: 24, l: -12, c: '#9fd8ff' }, { k: 'petal', x: 51, s: 13, d: 28, l: -2, c: '#ffb3c7' },
  { k: 'heart', x: 60, s: 16, d: 26, l: -21, c: '#ff8fbf' }, { k: 'star', x: 68, s: 12, d: 31, l: -7, c: '#ffe08a' },
  { k: 'petal', x: 76, s: 17, d: 23, l: -15, c: '#f9c2ff' }, { k: 'heart', x: 84, s: 14, d: 29, l: -25, c: '#ffa8cf' },
  { k: 'star', x: 91, s: 16, d: 26, l: -3, c: '#a9e4ff' }, { k: 'petal', x: 97, s: 12, d: 32, l: -19, c: '#ffcade' },
]
const SHAPE: Record<string, string> = {
  heart: 'M12 21s-7.5-4.6-9.6-9.2C.9 8.4 3 4.5 6.6 4.5c2.1 0 3.6 1.2 5.4 3.2 1.8-2 3.3-3.2 5.4-3.2 3.6 0 5.7 3.9 4.2 7.3C19.5 16.4 12 21 12 21z',
  star: 'M12 2.5l2.6 6.2 6.7.6-5.1 4.4 1.6 6.6L12 16.8 6.2 20.3l1.6-6.6L2.7 9.3l6.7-.6z',
  petal: 'M12 3c4 3 6 7 4.6 11.2C15.4 18 12 21 12 21s-3.4-3-4.6-6.8C6 10 8 6 12 3z',
}
</script>

<template>
  <div class="kw-bg" :class="{ paused }" aria-hidden="true">
    <div class="sun" />
    <div v-for="(c, i) in CLOUDS" :key="`c${i}`" class="cloud" :style="{ top: `${c.top}%`, animationDuration: `${c.d}s`, animationDelay: `${c.o}s` }">
      <svg :width="220 * c.s" :height="90 * c.s" viewBox="0 0 220 90">
        <path d="M30 78c-16 0-26-10-24-22 2-11 13-17 24-14 2-16 17-27 34-23 7-14 24-20 39-13 10-9 27-9 37 1 12-6 29 0 31 15 17-1 29 10 27 26-1 13-13 20-25 20z" fill="#ffffff" fill-opacity=".85" />
        <path d="M30 78h139c12 0 24-7 25-20-10 9-24 10-40 6-12 9-35 10-50 2-15 9-38 9-52 1-10 7-22 9-36 6 2 3 8 5 14 5z" fill="#f4dcef" fill-opacity=".6" />
      </svg>
    </div>
    <span v-for="(b, i) in BITS" :key="`b${i}`" class="bit" :style="{ left: `${b.x}%`, animationDuration: `${b.d}s`, animationDelay: `${b.l}s` }">
      <svg class="sway" :width="b.s" :height="b.s" viewBox="0 0 24 24" :style="{ animationDelay: `${b.l / 3}s` }"><path :d="SHAPE[b.k]" :fill="b.c" /></svg>
    </span>
  </div>
</template>

<style scoped>
.kw-bg {
  position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden;
  background:
    radial-gradient(circle at 85% 8%, rgba(255, 246, 200, .9), rgba(255, 246, 200, 0) 28%),
    linear-gradient(180deg, rgba(196, 228, 255, 1) 0%, rgba(232, 222, 255, 1) 45%, rgba(255, 224, 238, 1) 80%, rgba(255, 240, 246, 1) 100%);
}
.sun { position: absolute; right: 8%; top: 4%; width: 90px; height: 90px; border-radius: 50%; background: radial-gradient(circle, rgba(255, 244, 190, .95), rgba(255, 226, 150, .5) 60%, rgba(255, 226, 150, 0) 72%); }
.cloud { position: absolute; left: 0; animation: kwdrift linear infinite; will-change: transform; }
.cloud svg { display: block; }
.bit { position: absolute; bottom: -30px; animation: kwrise linear infinite; will-change: transform; opacity: .85; }
.sway { display: block; animation: kwsway 4s ease-in-out infinite alternate; }
.paused .cloud, .paused .bit, .paused .sway { animation-play-state: paused; }
@keyframes kwdrift { from { transform: translateX(-260px); } to { transform: translateX(110vw); } }
@keyframes kwrise { from { transform: translateY(0); opacity: 0; } 8% { opacity: .85; } 85% { opacity: .85; } to { transform: translateY(-110vh); opacity: 0; } }
@keyframes kwsway { from { transform: translateX(-10px) rotate(-14deg); } to { transform: translateX(10px) rotate(14deg); } }
@media (max-width: 640px) and (pointer: coarse) {
  .cloud, .bit, .sway { animation: none; }
  .bit { bottom: auto; top: 30%; opacity: .5; }
  .cloud { transform: translateX(20vw); }
}
@media (prefers-reduced-motion: reduce) {
  .cloud, .bit, .sway { animation: none; }
  .bit { bottom: auto; top: 30%; opacity: .5; }
  .cloud { transform: translateX(20vw); }
}
</style>

<style>
html.skin-kawaii body { background: transparent; font-family: "Nunito", "Varela Round", "Quicksand", "Comic Sans MS", system-ui, sans-serif; }
</style>
