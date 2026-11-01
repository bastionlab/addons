<script setup lang="ts">
/**
 * A voxel world behind the app. The sky follows the real clock: blue by day, orange at dawn/dusk, deep blue at
 * night with square twinkling stars and a square moon; a square sun/moon crosses the sky on an arc. Square pixel
 * clouds drift by. Two layers of stepped hills made of blocks (grass tops, dirt, stone, a few block trees) sit
 * at the bottom and darken with the time of day. All art is SVG built here (patterns on a 16-unit block grid).
 */
defineProps<{ path?: string }>()
const hidden = ref(false)
const now = ref(new Date())
let tick: ReturnType<typeof setInterval> | undefined
const onVis = () => { hidden.value = document.hidden; if (!document.hidden) now.value = new Date() }
onMounted(() => {
  onVis()
  document.addEventListener('visibilitychange', onVis)
  tick = setInterval(() => { if (!document.hidden) now.value = new Date() }, 60000)
})
onUnmounted(() => { document.removeEventListener('visibilitychange', onVis); clearInterval(tick) })

const hour = computed(() => now.value.getHours() + now.value.getMinutes() / 60)
type Phase = 'night' | 'dawn' | 'day' | 'dusk'
const phase = computed<Phase>(() => {
  const h = hour.value
  if (h < 5 || h >= 21) return 'night'
  if (h < 7.5) return 'dawn'
  if (h < 18) return 'day'
  return 'dusk'
})
// sun from 6:00 to 20:00, moon from 20:00 to 6:00; x left→right, y on an arc
function arc(t: number) { return { left: `${8 + t * 84}%`, top: `${62 - Math.sin(Math.PI * t) * 52}%` } }
const sun = computed(() => {
  const t = (hour.value - 6) / 14
  return t >= 0 && t <= 1 ? arc(t) : null
})
const moon = computed(() => {
  const h = hour.value
  const t = ((h >= 20 ? h - 20 : h + 4)) / 10
  return t >= 0 && t <= 1 ? arc(t) : null
})

// deterministic little noise so the world is the same every load
function rnd(seed: number) { const x = Math.sin(seed * 127.1) * 43758.5453; return x - Math.floor(x) }
const stars = Array.from({ length: 46 }, (_, i) => ({
  left: `${(rnd(i + 1) * 100).toFixed(1)}%`, top: `${(rnd(i + 51) * 58).toFixed(1)}%`,
  size: `${2 + Math.floor(rnd(i + 99) * 3)}px`, delay: `${(rnd(i + 7) * 4).toFixed(2)}s`,
}))

// clouds: blobs of 8-unit squares
const CLOUDS = [
  { rows: ['..XXXX....', '.XXXXXXXX.', 'XXXXXXXXXX', '..XXXXXX..'], top: '8%', dur: '150s', delay: '-20s', scale: 1 },
  { rows: ['...XXX..', '.XXXXXXX', 'XXXXXXXX'], top: '20%', dur: '190s', delay: '-110s', scale: .8 },
  { rows: ['.XXXXX.....', 'XXXXXXXXXX.', '.XXXXXXXXXX'], top: '31%', dur: '170s', delay: '-60s', scale: .65 },
  { rows: ['..XX..', 'XXXXXX'], top: '14%', dur: '230s', delay: '-160s', scale: .9 },
]
const clouds = CLOUDS.map(c => ({
  ...c,
  w: c.rows[0]!.length * 8,
  h: c.rows.length * 8,
  cells: c.rows.flatMap((r, y) => [...r].map((ch, x) => (ch === 'X' ? { x: x * 8, y: y * 8 } : null)).filter(Boolean) as { x: number, y: number }[]),
}))

// terrain: 40 columns of 16-unit blocks, 13 rows tall
const COLS = 40
const H = 208
function columns(f: (c: number) => number) {
  return Array.from({ length: COLS }, (_, c) => {
    const h = Math.max(1, Math.min(9, Math.round(f(c))))
    return { x: c * 16, top: H - h * 16, h }
  })
}
const near = columns(c => 3.2 + 1.8 * Math.sin(c * 0.33) + 1.1 * Math.sin(c * 0.91 + 1.3))
const far = columns(c => 5.2 + 2.2 * Math.sin(c * 0.21 + 2) + 1.3 * Math.sin(c * 0.67))
const TREE_COLS = [6, 17, 31]
const trees = TREE_COLS.map(c => ({ x: c * 16, base: near[c]!.top }))
</script>

<template>
  <div class="blocky-bd" :class="[phase, { paused: hidden }]" aria-hidden="true">
    <i class="sky s-day" /><i class="sky s-dawn" /><i class="sky s-dusk" /><i class="sky s-night" />

    <div class="stars">
      <i v-for="(s, i) in stars" :key="i" :style="{ left: s.left, top: s.top, width: s.size, height: s.size, animationDelay: s.delay }" />
    </div>

    <svg v-if="sun" class="orb sun" :style="sun" viewBox="0 0 32 32" shape-rendering="crispEdges">
      <rect x="0" y="0" width="32" height="32" fill="#ffe96b" opacity=".35" />
      <rect x="4" y="4" width="24" height="24" fill="#fff7b0" />
      <rect x="8" y="8" width="16" height="16" fill="#ffffff" />
    </svg>
    <svg v-if="moon" class="orb moon" :style="moon" viewBox="0 0 32 32" shape-rendering="crispEdges">
      <rect x="0" y="0" width="32" height="32" fill="#c8d4ff" opacity=".2" />
      <rect x="4" y="4" width="24" height="24" fill="#e8ecf7" />
      <rect x="8" y="8" width="6" height="6" fill="#b7bfd6" />
      <rect x="18" y="14" width="6" height="4" fill="#b7bfd6" />
      <rect x="10" y="20" width="4" height="4" fill="#c9cfe0" />
    </svg>

    <svg
      v-for="(c, i) in clouds" :key="i" class="cloud" :viewBox="`0 0 ${c.w} ${c.h}`" shape-rendering="crispEdges"
      :style="{ top: c.top, width: `${c.w * 2.4 * c.scale}px`, animationDuration: c.dur, animationDelay: c.delay }"
    >
      <rect v-for="(p, k) in c.cells" :key="k" :x="p.x" :y="p.y" width="8" height="8" fill="#ffffff" />
      <rect v-for="(p, k) in c.cells" :key="`s${k}`" :x="p.x" :y="p.y + 6" width="8" height="2" fill="#dfe6f2" />
    </svg>

    <svg class="land" :viewBox="`0 0 ${COLS * 16} ${H}`" preserveAspectRatio="xMidYMax slice" shape-rendering="crispEdges">
      <defs>
        <pattern id="skin-blocky-grass" width="16" height="16" patternUnits="userSpaceOnUse">
          <rect width="16" height="16" fill="#86603a" />
          <rect x="2" y="9" width="2" height="2" fill="#6b4a2b" /><rect x="10" y="12" width="2" height="2" fill="#a07448" /><rect x="6" y="13" width="2" height="2" fill="#6b4a2b" />
          <rect width="16" height="5" fill="#5fae3a" />
          <rect x="0" y="5" width="2" height="2" fill="#5fae3a" /><rect x="5" y="5" width="3" height="2" fill="#5fae3a" /><rect x="11" y="5" width="2" height="3" fill="#5fae3a" />
          <rect x="3" y="1" width="2" height="2" fill="#78c94e" /><rect x="9" y="2" width="2" height="2" fill="#4a9230" /><rect x="13" y="0" width="2" height="2" fill="#78c94e" />
        </pattern>
        <pattern id="skin-blocky-dirt" width="16" height="16" patternUnits="userSpaceOnUse">
          <rect width="16" height="16" fill="#86603a" />
          <rect x="1" y="2" width="2" height="2" fill="#6b4a2b" /><rect x="9" y="4" width="2" height="2" fill="#a07448" />
          <rect x="5" y="9" width="2" height="2" fill="#6b4a2b" /><rect x="12" y="11" width="2" height="2" fill="#6b4a2b" /><rect x="3" y="13" width="2" height="2" fill="#a07448" />
        </pattern>
        <pattern id="skin-blocky-stone" width="16" height="16" patternUnits="userSpaceOnUse">
          <rect width="16" height="16" fill="#7d7d7d" />
          <rect x="1" y="1" width="5" height="2" fill="#6a6a6a" /><rect x="9" y="5" width="4" height="2" fill="#929292" />
          <rect x="3" y="9" width="3" height="2" fill="#929292" /><rect x="10" y="11" width="5" height="2" fill="#6a6a6a" /><rect x="0" y="14" width="3" height="2" fill="#6a6a6a" />
        </pattern>
        <pattern id="skin-blocky-wood" width="16" height="16" patternUnits="userSpaceOnUse">
          <rect width="16" height="16" fill="#6b5030" />
          <rect x="3" y="0" width="2" height="16" fill="#563f24" /><rect x="10" y="0" width="2" height="16" fill="#7d5f3a" />
        </pattern>
        <pattern id="skin-blocky-leaf" width="16" height="16" patternUnits="userSpaceOnUse">
          <rect width="16" height="16" fill="#3f8a2a" />
          <rect x="2" y="2" width="3" height="3" fill="#2f6b1f" /><rect x="10" y="4" width="3" height="3" fill="#56a83a" />
          <rect x="5" y="10" width="3" height="3" fill="#56a83a" /><rect x="12" y="12" width="3" height="3" fill="#2f6b1f" />
        </pattern>
      </defs>
      <g class="far">
        <g v-for="c in far" :key="`f${c.x}`">
          <rect :x="c.x" :y="c.top" width="16" height="16" fill="url(#skin-blocky-grass)" />
          <rect :x="c.x" :y="c.top + 16" width="16" :height="H - c.top - 16" fill="url(#skin-blocky-stone)" />
        </g>
        <rect class="haze" x="0" y="0" :width="COLS * 16" :height="H" />
      </g>
      <g class="near">
        <g v-for="t in trees" :key="`t${t.x}`">
          <rect :x="t.x" :y="t.base - 48" width="16" height="48" fill="url(#skin-blocky-wood)" />
          <rect :x="t.x - 16" :y="t.base - 80" width="48" height="32" fill="url(#skin-blocky-leaf)" />
          <rect :x="t.x" :y="t.base - 96" width="16" height="16" fill="url(#skin-blocky-leaf)" />
        </g>
        <g v-for="c in near" :key="`n${c.x}`">
          <rect :x="c.x" :y="c.top" width="16" height="16" fill="url(#skin-blocky-grass)" />
          <rect :x="c.x" :y="c.top + 16" width="16" :height="Math.min(32, H - c.top - 16)" fill="url(#skin-blocky-dirt)" />
          <rect v-if="H - c.top > 48" :x="c.x" :y="c.top + 48" width="16" :height="H - c.top - 48" fill="url(#skin-blocky-stone)" />
          <rect :x="c.x" :y="c.top" width="16" height="1" fill="#ffffff" opacity=".18" />
        </g>
      </g>
    </svg>
    <i class="dark" />
  </div>
</template>

<style scoped>
.blocky-bd { position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; background: rgba(111, 156, 240, 1); }
.sky { position: absolute; inset: 0; opacity: 0; transition: opacity 4s steps(8); }
.s-day { background: linear-gradient(180deg, rgba(92, 146, 250, 1), rgba(160, 200, 255, 1) 70%); }
.s-dawn { background: linear-gradient(180deg, rgba(96, 110, 196, 1), rgba(240, 170, 130, 1) 65%, rgba(255, 205, 140, 1)); }
.s-dusk { background: linear-gradient(180deg, rgba(54, 60, 140, 1), rgba(214, 104, 72, 1) 62%, rgba(255, 160, 70, 1)); }
.s-night { background: linear-gradient(180deg, rgba(6, 8, 26, 1), rgba(20, 26, 66, 1) 70%); }
.day .s-day, .dawn .s-dawn, .dusk .s-dusk, .night .s-night { opacity: 1; }

.stars { position: absolute; inset: 0; opacity: 0; transition: opacity 4s steps(8); }
.night .stars { opacity: 1; }
.dusk .stars, .dawn .stars { opacity: .35; }
.stars i { position: absolute; background: rgba(255, 255, 255, 1); animation: twinkle 4s steps(2) infinite; }
@keyframes twinkle { 50% { opacity: .3; } }

.orb { position: absolute; width: 64px; height: 64px; margin: -32px 0 0 -32px; image-rendering: pixelated; }
.sun { filter: drop-shadow(0 0 18px rgba(255, 240, 150, .6)); }
.dusk .sun, .dawn .sun { filter: drop-shadow(0 0 22px rgba(255, 150, 60, .8)); }

.cloud { position: absolute; left: 0; height: auto; opacity: .92; animation: drift linear infinite; will-change: transform; }
.night .cloud { opacity: .35; }
.dusk .cloud, .dawn .cloud { opacity: .75; }
@keyframes drift { from { transform: translateX(-40vw); } to { transform: translateX(110vw); } }

.land { position: absolute; left: 0; right: 0; bottom: 0; width: 100%; height: 36vh; min-height: 200px; }
.far { transform: translateY(-34px); }
.haze { fill: rgba(170, 200, 255, .5); }
.dusk .haze, .dawn .haze { fill: rgba(240, 160, 120, .45); }
.night .haze { fill: rgba(20, 26, 66, .6); }
.dark { position: absolute; inset: 0; background: rgba(8, 10, 34, 1); opacity: 0; transition: opacity 4s steps(8); }
.night .dark { opacity: .45; }
.dusk .dark, .dawn .dark { opacity: .12; }

.paused .stars i, .paused .cloud { animation-play-state: paused; }
@media (prefers-reduced-motion: reduce) {
  .stars i, .cloud { animation: none; }
  .cloud { transform: translateX(20vw); }
  .sky, .stars, .dark { transition: none; }
}
@media (max-width: 640px) { .orb { width: 44px; height: 44px; margin: -22px 0 0 -22px; } .land { height: 30vh; } }
</style>
