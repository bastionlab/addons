<script setup lang="ts">
/** behind everything: an outrun night: twinkling stars, a striped sun, mountains, a neon grid floor rolling toward
 *  the viewer, and a dark veil so text on top stays readable */
defineProps<{ path?: string }>()
const hidden = ref(false)
const onVis = () => (hidden.value = document.hidden)
onMounted(() => { onVis(); document.addEventListener('visibilitychange', onVis) })
onUnmounted(() => document.removeEventListener('visibilitychange', onVis))
// stars from a fixed seed, so they sit still between reloads
let seed = 7
const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647)
const STARS = Array.from({ length: 46 }, () => ({
  left: `${(rnd() * 100).toFixed(2)}%`, top: `${(rnd() * 56).toFixed(2)}%`,
  size: `${(1 + rnd() * 2).toFixed(1)}px`, delay: `${(-rnd() * 4).toFixed(2)}s`, dur: `${(2.5 + rnd() * 3).toFixed(2)}s`,
}))
</script>

<template>
  <div class="sw-bd" :class="{ paused: hidden }" aria-hidden="true">
    <div class="sky" />
    <div class="stars">
      <i v-for="(s, i) in STARS" :key="i" :style="{ left: s.left, top: s.top, width: s.size, height: s.size, animationDelay: s.delay, animationDuration: s.dur }" />
    </div>
    <div class="sun" />
    <svg class="mtn" viewBox="0 0 1200 160" preserveAspectRatio="none">
      <path d="M0 160V96l70-30 60 22 90-62 70 48 50-20 80 52 70-40 90-58 80 64 60-26 90 44 70-54 80 36 60-18 90 46 70-30 70 20v76z" fill="rgb(46,16,84)" />
      <path d="M0 160v-40l90-40 70 30 110-56 80 50 60-18 90 46 100-62 80 48 70-24 100 44 80-38 90 30 60-14 70 26 50-10v104z" fill="rgb(20,8,42)" />
      <path d="M0 120l90-40 70 30 110-56 80 50 60-18 90 46 100-62 80 48 70-24 100 44 80-38 90 30 60-14 70 26 50-10" fill="none" stroke="rgb(255,79,216)" stroke-opacity=".7" stroke-width="2" vector-effect="non-scaling-stroke" />
    </svg>
    <div class="floor"><div class="plane" /><div class="haze" /></div>
    <div class="veil" />
  </div>
</template>

<style scoped>
.sw-bd { --hz: 36%; position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; background: var(--bg); }
.sky { position: absolute; inset: 0; background: linear-gradient(180deg, rgb(8 3 22) 0%, rgb(30 8 58) 38%, rgb(92 18 112) 56%, rgb(200 40 140) 64%); }
.stars { position: absolute; inset: 0; }
.stars i { position: absolute; border-radius: 50%; background: rgb(255 240 255); box-shadow: 0 0 4px rgb(255 200 255); animation: sw-twinkle 3s ease-in-out infinite; }
@keyframes sw-twinkle { 50% { opacity: .2; transform: scale(.6); } }
.sun {
  position: absolute; left: 50%; bottom: calc(var(--hz) - 4%); width: min(44vmin, 380px); aspect-ratio: 1; transform: translateX(-50%);
  border-radius: 50%; background: linear-gradient(180deg, rgb(255 238 120) 0%, rgb(255 150 70) 42%, rgb(255 60 160) 78%, rgb(200 30 170) 100%);
  box-shadow: 0 0 60px rgba(255, 90, 170, .55), 0 0 140px rgba(255, 120, 80, .3);
  -webkit-mask-image: linear-gradient(180deg, black 0 48%, transparent 48% 51%, black 51% 59%, transparent 59% 63%, black 63% 69%, transparent 69% 74%, black 74% 79%, transparent 79% 85%, black 85% 88%, transparent 88%);
  mask-image: linear-gradient(180deg, black 0 48%, transparent 48% 51%, black 51% 59%, transparent 59% 63%, black 63% 69%, transparent 69% 74%, black 74% 79%, transparent 79% 85%, black 85% 88%, transparent 88%);
}
.mtn { position: absolute; left: 0; width: 100%; bottom: calc(var(--hz) - 1px); height: 13vh; min-height: 70px; }
.floor { position: absolute; left: 0; right: 0; bottom: 0; height: var(--hz); overflow: hidden; perspective: 240px; perspective-origin: 50% 0; background: linear-gradient(180deg, rgb(40 8 64), rgb(10 3 22)); }
.plane {
  position: absolute; left: -100%; width: 300%; bottom: 0; height: 500%; transform-origin: 50% 100%; transform: rotateX(80deg);
  background-image: linear-gradient(90deg, rgba(255, 79, 216, .8) 2px, transparent 2px), linear-gradient(0deg, rgba(255, 79, 216, .8) 2px, transparent 2px);
  background-size: 64px 64px; background-position: center bottom;
  animation: sw-run 1.4s linear infinite;
}
@keyframes sw-run { from { transform: rotateX(80deg) translateY(0); } to { transform: rotateX(80deg) translateY(64px); } }
.haze { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(255, 70, 190, .55), rgba(40, 8, 64, .2) 22%, transparent 45%); }
.veil { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(8, 3, 20, .55), rgba(8, 3, 20, .3) 55%, rgba(8, 3, 20, .5)); }
.paused .stars i, .paused .plane { animation-play-state: paused; }
@media (max-width: 640px) {
  .sw-bd { --hz: 30%; }
  .sun { width: 62vw; }
  .stars i:nth-child(2n) { display: none; }
}
@media (prefers-reduced-motion: reduce) { .stars i, .plane { animation: none; } }
</style>
