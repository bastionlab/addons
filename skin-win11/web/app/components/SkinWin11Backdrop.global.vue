<script setup lang="ts">
/** an original "bloom" wallpaper: soft ribbon petals in blues opening from the centre, drifting very slowly */
defineProps<{ path?: string }>()
const paused = ref(false)
const onVis = () => (paused.value = document.hidden)
onMounted(() => { onVis(); document.addEventListener('visibilitychange', onVis) })
onUnmounted(() => document.removeEventListener('visibilitychange', onVis))
// petals: angle around the bloom, length and which gradient; drawn as one ribbon path rotated into place
const PETALS = [
  { a: -78, s: 1.0, g: 'a' }, { a: -48, s: .92, g: 'b' }, { a: -18, s: 1.04, g: 'c' }, { a: 12, s: .9, g: 'a' },
  { a: 42, s: 1.0, g: 'b' }, { a: 72, s: .86, g: 'c' }, { a: 102, s: .95, g: 'a' }, { a: 132, s: .9, g: 'b' },
  { a: 162, s: 1.02, g: 'c' }, { a: 192, s: .88, g: 'a' }, { a: 222, s: .97, g: 'b' }, { a: 252, s: .9, g: 'c' },
]
</script>

<template>
  <div class="w11-bg" :class="{ paused }" aria-hidden="true">
    <svg class="sky" viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice" width="100%" height="100%"><defs>
        <radialGradient id="w11-sky" cx="50%" cy="58%" r="75%">
          <stop offset="0" stop-color="#1b3f86" />
          <stop offset=".45" stop-color="#0f2453" />
          <stop offset="1" stop-color="#060c1d" />
        </radialGradient>
      </defs><rect width="1600" height="1000" fill="url(#w11-sky)" /></svg>
    <svg class="flower" viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice" width="100%" height="100%">
      <defs>
        <linearGradient id="w11-pa" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stop-color="#2f7cf6" stop-opacity=".0" />
          <stop offset=".35" stop-color="#3d8bff" stop-opacity=".75" />
          <stop offset="1" stop-color="#9fd8ff" stop-opacity=".95" />
        </linearGradient>
        <linearGradient id="w11-pb" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stop-color="#1747b8" stop-opacity="0" />
          <stop offset=".4" stop-color="#2463e0" stop-opacity=".7" />
          <stop offset="1" stop-color="#6fb6ff" stop-opacity=".9" />
        </linearGradient>
        <linearGradient id="w11-pc" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stop-color="#0c2f8a" stop-opacity="0" />
          <stop offset=".45" stop-color="#1d56c9" stop-opacity=".6" />
          <stop offset="1" stop-color="#c5e8ff" stop-opacity=".85" />
        </linearGradient>
        <radialGradient id="w11-core" cx="50%" cy="50%" r="50%">
          <stop offset="0" stop-color="#e6f5ff" stop-opacity=".9" />
          <stop offset=".35" stop-color="#7cc4ff" stop-opacity=".45" />
          <stop offset="1" stop-color="#2a6be0" stop-opacity="0" />
        </radialGradient>
      </defs>
      <g transform="translate(800 590)">
        <g>
          <g v-for="(p, i) in PETALS" :key="i" :transform="`rotate(${p.a}) scale(${p.s})`">
            <g>
              <path d="M0 0 C 90 -70, 250 -95, 420 -30 C 330 -10, 210 20, 120 50 C 70 45, 25 25, 0 0 Z" :fill="`url(#w11-p${p.g})`" />
              <path d="M10 2 C 120 -40, 260 -60, 400 -28" fill="none" stroke="#d8efff" stroke-opacity=".35" stroke-width="2" />
            </g>
          </g>
          <g v-for="(p, i) in PETALS" :key="`in${i}`" :transform="`rotate(${p.a + 15}) scale(${p.s * .58})`" opacity=".8">
            <path d="M0 0 C 90 -70, 250 -95, 420 -30 C 330 -10, 210 20, 120 50 C 70 45, 25 25, 0 0 Z" :fill="`url(#w11-p${p.g === 'a' ? 'c' : 'a'})`" />
          </g>
          <circle r="120" fill="url(#w11-core)" />
        </g>
      </g>
    </svg>
    <div class="veil" />
  </div>
</template>

<style scoped>
.w11-bg { position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; background: var(--bg); }
.w11-bg svg { display: block; }
.sky, .flower { position: absolute; inset: 0; }
/* the whole bloom turns and breathes as one composited layer: cheap on phones */
.flower { animation: w11turn 80s ease-in-out infinite alternate; will-change: transform; transform-origin: 50% 59%; }
.paused .flower { animation-play-state: paused; }
/* readability over the bright core */
.veil { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(4, 10, 26, .35), rgba(4, 10, 26, .15) 40%, rgba(4, 10, 26, .45)); }
@keyframes w11turn { from { transform: rotate(-5deg) scale(1.08); } 50% { transform: rotate(0deg) scale(1.13); } to { transform: rotate(5deg) scale(1.08); } }
@media (prefers-reduced-motion: reduce) { .flower { animation: none; } }
</style>
