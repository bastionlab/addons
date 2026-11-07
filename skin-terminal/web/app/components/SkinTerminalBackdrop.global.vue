<script setup lang="ts">
/**
 * Behind everything: a black phosphor screen with a faint green glow and a very quiet matrix rain on a small
 * canvas (≤ 18 fps, drawn at a coarse grid, paused when the tab is hidden, never started under reduced motion).
 */
defineProps<{ path?: string }>()
const cv = ref<HTMLCanvasElement | null>(null)
const GLYPHS = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789<>/=$#*+'
const FS = 15
let raf = 0
let last = 0
let drops: number[] = []
let ctx: CanvasRenderingContext2D | null = null
let reduced = false
let phoneMq: MediaQueryList | null = null
const phone = ref(false)

function size() {
  const c = cv.value
  if (!c) return
  c.width = Math.ceil(window.innerWidth / 1.5)
  c.height = Math.ceil(window.innerHeight / 1.5)
  ctx = c.getContext('2d')
  const cols = Math.ceil(c.width / FS)
  drops = Array.from({ length: cols }, (_, i) => drops[i] ?? Math.random() * -60)
  if (ctx) { ctx.fillStyle = 'rgb(2, 8, 4)'; ctx.fillRect(0, 0, c.width, c.height) }
}
function frame(t: number) {
  raf = requestAnimationFrame(frame)
  if (t - last < 56) return // ~18 fps
  last = t
  const c = cv.value
  if (!c || !ctx) return
  ctx.fillStyle = 'rgba(2, 8, 4, 0.12)'
  ctx.fillRect(0, 0, c.width, c.height)
  ctx.font = `${FS - 3}px monospace`
  for (let i = 0; i < drops.length; i++) {
    const y = drops[i]! * FS
    if (y > 0) {
      const ch = GLYPHS[(Math.random() * GLYPHS.length) | 0]!
      ctx.fillStyle = Math.random() < 0.06 ? 'rgb(210, 255, 220)' : 'rgb(57, 255, 106)'
      ctx.fillText(ch, i * FS, y)
    }
    if (y > c.height && Math.random() > 0.975) drops[i] = Math.random() * -20
    else drops[i]! += 0.5 + (i % 3) * 0.18
  }
}
function start() { if (!raf && !reduced && !phone.value && !document.hidden) raf = requestAnimationFrame(frame) }
function stop() { if (raf) cancelAnimationFrame(raf); raf = 0 }
const onVis = () => (document.hidden ? stop() : start())
const onResize = () => { if (!phone.value) size() }
// phones get no rain at all: no rAF loop, canvas hidden
const onPhone = () => {
  phone.value = !!phoneMq?.matches
  if (phone.value) stop()
  else { size(); start() }
}
onMounted(() => {
  reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduced) return
  phoneMq = window.matchMedia('(max-width: 640px), (pointer: coarse)')
  phone.value = phoneMq.matches
  phoneMq.addEventListener('change', onPhone)
  if (!phone.value) { size(); start() }
  document.addEventListener('visibilitychange', onVis)
  window.addEventListener('resize', onResize, { passive: true })
})
onUnmounted(() => {
  stop()
  phoneMq?.removeEventListener('change', onPhone)
  document.removeEventListener('visibilitychange', onVis)
  window.removeEventListener('resize', onResize)
})
</script>

<template>
  <div class="tm-bd" aria-hidden="true">
    <canvas v-show="!phone" ref="cv" class="rain" />
    <div class="glow" />
  </div>
</template>

<style scoped>
.tm-bd { position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; background: var(--bg); }
.rain { position: absolute; inset: 0; width: 100%; height: 100%; opacity: .16; image-rendering: pixelated; }
.glow { position: absolute; inset: 0; background: radial-gradient(120% 90% at 50% 45%, rgba(57, 255, 106, .07), transparent 60%); }
@media (max-width: 640px) { .rain { opacity: .12; } }
@media (prefers-reduced-motion: reduce) { .rain { display: none; } }
</style>
