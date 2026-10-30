<script setup lang="ts">
/**
 * The club: a perspective dance floor whose tiles light up in rotating colours, a mirror ball hanging from the top
 * on a string (its facets slide past = spinning, its sparkles wheel across the walls), and soft coloured spots
 * sweeping the room. Easter egg: tap the ball 5 times → 5 s of party mode (more lights, faster ball, faster floor);
 * the Nav shows the "Party mode!" line. The layer itself never takes pointer events: taps are read from a
 * document listener that checks whether the (non-interactive) spot under the finger is the ball.
 */
defineProps<{ path?: string }>()
const party = useState('skinDisco:party', () => false)
const hidden = ref(false)
const tapped = ref(false)
const ball = ref<HTMLElement | null>(null)

// floor: 10 × 6 tiles, two colour layers each, staggered so colour waves roll diagonally across the floor
const COLS = 10
const ROWS = 6
const LIGHTS = ['rgba(255, 63, 180, .95)', 'rgba(63, 216, 255, .95)', 'rgba(255, 201, 63, .95)', 'rgba(180, 75, 255, .95)', 'rgba(63, 242, 160, .95)']
const tiles = Array.from({ length: COLS * ROWS }, (_, i) => {
  const r = Math.floor(i / COLS)
  const c = i % COLS
  const k = r + c
  return {
    '--a': LIGHTS[k % LIGHTS.length],
    '--b': LIGHTS[(k + 2) % LIGHTS.length],
    '--d1': `${((k * 0.23) % 2.4).toFixed(2)}s`,
    '--d2': `${(((i * 37) % 24) / 10 + 1.2).toFixed(2)}s`,
  }
})

// mirror ball facets: rows of little mirrors, one horizontal period (6 facets) wide so the slide loops seamlessly
const GREYS = ['#f4f1ff', '#c9c3dd', '#8f88a8', '#e2ddf2', '#6d6588', '#b3acc9', '#ffffff', '#ffd7f0', '#d4f4ff']
const facets: { x: number, y: number, f: string }[] = []
for (let r = 0; r < 12; r++) {
  for (let c = -6; c < 19; c++) {
    const m = ((c % 6) + 6) % 6
    facets.push({ x: c * 8 + (r % 2 ? 4 : 0), y: r * 8 + 2, f: GREYS[(r * 5 + m * 3) % GREYS.length]! })
  }
}

const isInteractive = (el: Element | null) => !!el?.closest?.('a, button, input, select, textarea, label, summary, [role="button"], [contenteditable], .panel, .topic')
let taps = 0
let last = 0
const timers = new Set<ReturnType<typeof setTimeout>>()
function later(fn: () => void, ms: number) {
  const tm = setTimeout(() => { timers.delete(tm); fn() }, ms)
  timers.add(tm)
}
function onDown(e: PointerEvent) {
  const b = ball.value
  if (!b || isInteractive(e.target as Element | null)) return
  const r = b.getBoundingClientRect()
  if (e.clientX < r.left - 8 || e.clientX > r.right + 8 || e.clientY < r.top - 8 || e.clientY > r.bottom + 8) return
  const now = Date.now()
  taps = now - last > 1500 ? 1 : taps + 1
  last = now
  tapped.value = true
  later(() => (tapped.value = false), 220)
  if (taps >= 5 && !party.value) {
    taps = 0
    party.value = true
    later(() => (party.value = false), 5000)
  }
}
const onVis = () => {
  hidden.value = document.hidden
  document.documentElement.classList.toggle('disco-paused', document.hidden)
}
onMounted(() => {
  onVis()
  document.addEventListener('visibilitychange', onVis)
  document.addEventListener('pointerdown', onDown)
})
onUnmounted(() => {
  document.removeEventListener('visibilitychange', onVis)
  document.removeEventListener('pointerdown', onDown)
  document.documentElement.classList.remove('disco-paused')
  for (const tm of timers) clearTimeout(tm)
  timers.clear()
  party.value = false
})
</script>

<template>
  <div class="disco-bd" :class="{ party, paused: hidden }" aria-hidden="true">
    <i class="haze" />
    <i class="sparkles" />
    <i class="spot s1" /><i class="spot s2" /><i class="spot s3" />
    <i class="spot s4 extra" /><i class="spot s5 extra" /><i class="spot s6 extra" />

    <div class="floor-wrap">
      <div class="floor">
        <i v-for="(t, i) in tiles" :key="i" class="tile" :style="t" />
      </div>
    </div>

    <div ref="ball" class="ball-wrap" :class="{ tapped }">
      <i class="string" />
      <div class="ball-swing">
        <svg class="ball" viewBox="0 0 100 100">
          <defs>
            <clipPath id="skin-disco-ball-clip"><circle cx="50" cy="50" r="46" /></clipPath>
            <radialGradient id="skin-disco-ball-shade" cx="36%" cy="30%" r="78%">
              <stop offset="0" stop-color="#ffffff" stop-opacity=".55" />
              <stop offset=".35" stop-color="#ffffff" stop-opacity="0" />
              <stop offset=".8" stop-color="#140a24" stop-opacity=".45" />
              <stop offset="1" stop-color="#140a24" stop-opacity=".85" />
            </radialGradient>
          </defs>
          <rect x="46" y="-2" width="8" height="7" rx="1.5" fill="#b9b2cf" />
          <circle cx="50" cy="50" r="47" fill="#3b3356" />
          <g clip-path="url(#skin-disco-ball-clip)">
            <g class="facets">
              <rect v-for="(f, i) in facets" :key="i" :x="f.x" :y="f.y" width="7" height="7" rx=".8" :fill="f.f" />
            </g>
          </g>
          <circle cx="50" cy="50" r="46" fill="url(#skin-disco-ball-shade)" />
          <g class="glints" fill="#ffffff">
            <path class="g1" d="M30 22 l1.6 5 5 1.6 -5 1.6 -1.6 5 -1.6 -5 -5 -1.6 5 -1.6z" />
            <path class="g2" d="M68 40 l1.2 3.8 3.8 1.2 -3.8 1.2 -1.2 3.8 -1.2 -3.8 -3.8 -1.2 3.8 -1.2z" />
            <path class="g3" d="M44 70 l1 3 3 1 -3 1 -1 3 -1 -3 -3 -1 3 -1z" />
          </g>
        </svg>
      </div>
    </div>
  </div>
</template>

<style scoped>
.disco-bd {
  position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden;
  background: radial-gradient(120% 70% at 50% 0%, rgba(58, 22, 92, 1) 0%, var(--bg) 60%);
  --bx: calc(50% + var(--disco-side, 0px) / 2);
  --by: var(--disco-ball-y, 62px);
}
.haze { position: absolute; inset: 0; background: radial-gradient(60% 40% at 50% 100%, rgba(255, 63, 180, .18), rgba(255, 63, 180, 0) 70%); }

/* mirror-ball reflections: a dot field centred on the ball, wheeling round it */
.sparkles {
  position: absolute; left: var(--bx); top: var(--by); width: 220vmax; height: 220vmax; margin: -110vmax 0 0 -110vmax;
  background:
    radial-gradient(circle, rgba(255, 255, 255, .55) 0 1.4px, rgba(255, 255, 255, 0) 2.4px) 0 0 / 83px 71px,
    radial-gradient(circle, rgba(255, 170, 230, .45) 0 1.2px, rgba(255, 170, 230, 0) 2.2px) 31px 17px / 127px 109px,
    radial-gradient(circle, rgba(150, 230, 255, .45) 0 1.2px, rgba(150, 230, 255, 0) 2.2px) 57px 44px / 149px 97px;
  -webkit-mask-image: radial-gradient(circle, rgba(0, 0, 0, 0) 3%, rgba(0, 0, 0, .9) 8%, rgba(0, 0, 0, .5) 30%, rgba(0, 0, 0, 0) 48%);
  mask-image: radial-gradient(circle, rgba(0, 0, 0, 0) 3%, rgba(0, 0, 0, .9) 8%, rgba(0, 0, 0, .5) 30%, rgba(0, 0, 0, 0) 48%);
  animation: dspin 90s linear infinite; will-change: transform;
}

/* sweeping light spots */
.spot { position: absolute; width: 70vmax; height: 70vmax; margin: -35vmax 0 0 -35vmax; border-radius: 50%; mix-blend-mode: screen; opacity: .28; will-change: transform; }
.s1 { left: 20%; top: 30%; background: radial-gradient(circle, rgba(255, 63, 180, .9), rgba(255, 63, 180, 0) 60%); animation: sweep1 26s ease-in-out infinite alternate; }
.s2 { left: 80%; top: 45%; background: radial-gradient(circle, rgba(63, 216, 255, .85), rgba(63, 216, 255, 0) 60%); animation: sweep2 31s ease-in-out infinite alternate; }
.s3 { left: 50%; top: 80%; background: radial-gradient(circle, rgba(255, 201, 63, .7), rgba(255, 201, 63, 0) 60%); animation: sweep3 23s ease-in-out infinite alternate; opacity: .2; }
.extra { opacity: 0; transition: opacity .4s; width: 40vmax; height: 40vmax; margin: -20vmax 0 0 -20vmax; }
.s4 { left: 10%; top: 10%; background: radial-gradient(circle, rgba(180, 75, 255, .9), rgba(180, 75, 255, 0) 60%); animation: sweep2 3.2s ease-in-out infinite alternate; }
.s5 { left: 85%; top: 20%; background: radial-gradient(circle, rgba(63, 242, 160, .8), rgba(63, 242, 160, 0) 60%); animation: sweep1 2.6s ease-in-out infinite alternate; }
.s6 { left: 55%; top: 60%; background: radial-gradient(circle, rgba(255, 90, 90, .8), rgba(255, 90, 90, 0) 60%); animation: sweep3 2.9s ease-in-out infinite alternate; }
.party .extra { opacity: .4; }
.party .spot:not(.extra) { opacity: .4; }
@keyframes sweep1 { from { transform: translate(-10vw, -8vh) scale(.9); } to { transform: translate(45vw, 25vh) scale(1.1); } }
@keyframes sweep2 { from { transform: translate(8vw, -20vh); } to { transform: translate(-50vw, 18vh) scale(.85); } }
@keyframes sweep3 { from { transform: translate(-30vw, 0) scale(1.1); } to { transform: translate(30vw, -30vh) scale(.9); } }
@keyframes dspin { to { transform: rotate(360deg); } }

/* dance floor */
.floor-wrap {
  position: absolute; left: var(--disco-side, 0px); right: 0; bottom: 0; height: 44vh; perspective: 420px; perspective-origin: 50% 0%;
  -webkit-mask-image: linear-gradient(to top, rgba(0, 0, 0, .95) 30%, rgba(0, 0, 0, 0));
  mask-image: linear-gradient(to top, rgba(0, 0, 0, .95) 30%, rgba(0, 0, 0, 0));
}
.floor {
  position: absolute; left: -35%; right: -35%; bottom: -6%; height: 150%;
  display: grid; grid-template-columns: repeat(10, 1fr); grid-template-rows: repeat(6, 1fr); gap: 4px; padding: 4px;
  background: rgba(10, 4, 20, 1); transform: rotateX(64deg); transform-origin: 50% 100%;
}
.tile { position: relative; background: rgba(40, 22, 70, 1); border-radius: 2px; }
.tile::before, .tile::after { content: ''; position: absolute; inset: 0; border-radius: 2px; opacity: 0; will-change: opacity; }
.tile::before { background: var(--a); box-shadow: 0 0 18px var(--a); animation: lit 2.4s ease-in-out var(--d1) infinite; }
.tile::after { background: var(--b); animation: lit 3.6s ease-in-out var(--d2) infinite; }
.party .tile::before { animation-duration: .6s; }
.party .tile::after { animation-duration: .9s; }
@keyframes lit { 0%, 100% { opacity: .05; } 40% { opacity: .75; } 60% { opacity: .55; } }

/* mirror ball */
.ball-wrap { position: absolute; left: var(--bx); top: 0; width: var(--disco-ball, 64px); margin-left: calc(var(--disco-ball, 64px) / -2); display: flex; flex-direction: column; align-items: center; }
.string { display: block; width: 2px; height: calc(var(--by) - var(--disco-ball, 64px) / 2); background: linear-gradient(rgba(200, 190, 230, .2), rgba(200, 190, 230, .8)); }
.ball-swing { width: 100%; transform-origin: 50% -40px; animation: swing 6s ease-in-out infinite alternate; }
.tapped .ball-swing { animation: jiggle .22s ease-out; }
.ball { display: block; width: 100%; height: auto; overflow: visible; filter: drop-shadow(0 0 14px rgba(255, 180, 240, .45)); }
.facets { animation: facets 7s linear infinite; }
.party .facets { animation-duration: 1.2s; }
.party .ball { filter: drop-shadow(0 0 22px rgba(255, 120, 220, .8)); }
@keyframes facets { to { transform: translateX(-48px); } }
@keyframes swing { from { transform: rotate(-2deg); } to { transform: rotate(2deg); } }
@keyframes jiggle { 0% { transform: scale(1); } 40% { transform: scale(1.12) rotate(4deg); } 100% { transform: scale(1); } }
.glints path { transform-box: fill-box; transform-origin: center; animation: glint 2.8s ease-in-out infinite; opacity: 0; }
.glints .g2 { animation-delay: .9s; }
.glints .g3 { animation-delay: 1.9s; }
@keyframes glint { 0%, 70%, 100% { opacity: 0; transform: scale(.3); } 80% { opacity: 1; transform: scale(1.2) rotate(45deg); } }

.paused *, .paused *::before, .paused *::after { animation-play-state: paused !important; }
@media (prefers-reduced-motion: reduce) {
  .sparkles, .spot, .facets, .ball-swing, .glints path, .tile::before, .tile::after { animation: none !important; }
  .tile::before { opacity: .35; }
  .glints path { opacity: .8; }
}
</style>

<style>
/* geometry the backdrop shares with the nav and frame; only while this skin is on */
html.skin-disco { --disco-ball: 64px; --disco-ball-y: 66px; }
@media (min-width: 961px) { html.skin-disco { --disco-side: 236px; } }
@media (min-width: 641px) and (max-width: 960px) { html.skin-disco { --disco-side: 96px; } }
@media (max-width: 640px) { html.skin-disco { --disco-side: 0px; --disco-ball: 42px; --disco-ball-y: 28px; } }
html.skin-disco.disco-paused .dpanel *, html.skin-disco.disco-paused .dpanel::before { animation-play-state: paused !important; }
</style>
