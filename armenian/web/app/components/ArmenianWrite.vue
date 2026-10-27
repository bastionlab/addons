<script setup lang="ts">
/**
 * Write card input: a guided trace pad. Without Hint the pad is blank (from memory); Hint shows the target glyph as
 * a faint ghost to trace. Check rasterises the glyph and scores the ink against it (coverage / spill, see
 * utils/armenianTrace.ts). Words also have an on-screen Armenian keyboard, checked by exact match (case/space
 * normalised); either may be used.
 */
import type { ArmCard } from '../utils/armenian'
const props = defineProps<{ c: ArmCard, locked?: boolean }>()
const emit = defineEmits<{ check: [{ ok: boolean, typed: string, cov?: number, hint: boolean, sugg: number }] }>()

const typed = ref('')
const word = computed(() => props.c.t === 'w')
const target = computed(() => answerOf(props.c))
const keys = LETTERS
const FONT = "'Noto Sans Armenian', 'DejaVu Sans', sans-serif"

const type = (k: string) => { if (!props.locked && typed.value.length < 60) typed.value += k }
const back = () => { if (!props.locked) typed.value = [...typed.value].slice(0, -1).join('') }

// --- pad: guide canvas (ghost, reveal) under the ink canvas ---
const cv = ref<HTMLCanvasElement>()
const gcv = ref<HTMLCanvasElement>()
let ctx: CanvasRenderingContext2D | null = null
let last: [number, number] | null = null
let W = 0, H = 0
const inked = ref(false)
const hinted = ref(false) // Hint used on this card (the card remounts per card)
const showHint = ref(false)
let revealed = false

function setup() {
  const el = cv.value!, g = gcv.value!, r = el.getBoundingClientRect(), dpr = window.devicePixelRatio || 1
  W = Math.round(r.width); H = Math.round(r.height)
  for (const c of [el, g]) { c.width = Math.round(r.width * dpr); c.height = Math.round(r.height * dpr) }
  ctx = el.getContext('2d')!
  ctx.scale(dpr, dpr)
  ctx.lineWidth = 5; ctx.lineCap = 'round'; ctx.lineJoin = 'round'
  ctx.strokeStyle = getComputedStyle(el).color
  g.getContext('2d')!.scale(dpr, dpr)
}
const at = (e: PointerEvent): [number, number] => { const r = cv.value!.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top] }
function down(e: PointerEvent) {
  if (props.locked) return
  cv.value!.setPointerCapture(e.pointerId)
  last = at(e); inked.value = true
  ctx!.beginPath(); ctx!.arc(last[0], last[1], 2.5, 0, 7); ctx!.fillStyle = ctx!.strokeStyle; ctx!.fill()
}
function move(e: PointerEvent) {
  if (!last) return
  for (const c of (e.getCoalescedEvents?.() ?? [e])) {
    const p = at(c)
    ctx!.beginPath(); ctx!.moveTo(last[0], last[1]); ctx!.lineTo(p[0], p[1]); ctx!.stroke()
    last = p
  }
}
const up = () => { last = null }
function clear() { ctx!.clearRect(0, 0, W, H); inked.value = false }

/** the target glyph, auto-sized to fill the canvas, centred, thickened with a stroke so a finger can follow it */
function paintGlyph(c: CanvasRenderingContext2D, fill: string) {
  const text = target.value
  c.font = `100px ${FONT}`
  const m = c.measureText(text)
  const asc = m.actualBoundingBoxAscent || 75, desc = m.actualBoundingBoxDescent || 0
  const k = Math.min((W * 0.9) / (m.width || 100), (H * 0.8) / (asc + desc || 100))
  c.font = `${100 * k}px ${FONT}`
  c.textAlign = 'center'; c.textBaseline = 'alphabetic'
  c.fillStyle = fill; c.strokeStyle = fill; c.lineWidth = Math.max(4, 100 * k * 0.06); c.lineJoin = 'round'
  const y = H / 2 + ((asc - desc) * k) / 2
  c.strokeText(text, W / 2, y); c.fillText(text, W / 2, y)
}
function drawGuide() {
  const g = gcv.value!.getContext('2d')!
  g.save(); g.clearRect(0, 0, W, H)
  if (showHint.value && !revealed) { g.globalAlpha = 0.16; paintGlyph(g, getComputedStyle(gcv.value!).color) }
  g.restore()
}
function toggleHint() {
  if (props.locked) return
  showHint.value = !showHint.value
  if (showHint.value) hinted.value = true
  drawGuide()
}
/** the target in the accent colour over the ink (after Check / giving up) */
function reveal() {
  if (revealed || !ctx) return
  revealed = true
  drawGuide()
  ctx.save(); ctx.globalAlpha = 0.55; paintGlyph(ctx, getComputedStyle(cv.value!).getPropertyValue('--accent').trim() || '#4c8dff'); ctx.restore()
}
watch(() => props.locked, (l) => { if (l) reveal() })

/** CSS-pixel masks of the glyph and of the ink */
function masks() {
  const mk = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; return c }
  const gc = mk(), ic = mk()
  const g = gc.getContext('2d', { willReadFrequently: true })!, i = ic.getContext('2d', { willReadFrequently: true })!
  paintGlyph(g, '#000')
  i.drawImage(cv.value!, 0, 0, W, H)
  const bits = (c: CanvasRenderingContext2D) => { const d = c.getImageData(0, 0, W, H).data, o = new Uint8Array(W * H); for (let n = 0; n < o.length; n++) o[n] = d[n * 4 + 3]! > 100 ? 1 : 0; return o }
  return { glyph: bits(g), ink: bits(i) }
}

const canCheck = computed(() => inked.value || !!norm(typed.value))
function check() {
  if (props.locked || !canCheck.value) return
  let cov: number | undefined, pass = false
  if (inked.value) { const { glyph, ink } = masks(); const s = traceScore(glyph, ink, W, H); cov = s.cov; pass = s.pass }
  const typedOk = !!norm(typed.value) && norm(typed.value) === norm(target.value)
  const ok = norm(typed.value) ? typedOk || pass : pass
  // pass = Good (Easy when done from memory and clean), fail = Again; the hint caps it at Good
  let sugg = ok ? ((!hinted.value && (typedOk || (cov ?? 0) >= 0.8)) ? 4 : 3) : 1
  if (hinted.value) sugg = Math.min(sugg, 3)
  emit('check', { ok, typed: typed.value, cov, hint: hinted.value, sugg })
}
onMounted(setup)
defineExpose({ typed, check, canCheck, toggleHint, showHint, hinted, reveal })
</script>

<template>
  <div class="aw">
    <div class="padwrap">
      <canvas ref="gcv" class="pad guide" />
      <canvas ref="cv" class="pad ink" @pointerdown.prevent="down" @pointermove="move" @pointerup="up" @pointercancel="up" />
      <button type="button" class="btn sm ghost clr" :disabled="!inked || locked" @click="clear">Clear</button>
    </div>
    <template v-if="word">
      <div lang="hy" class="typed" :class="{ empty: !typed }">{{ typed || 'Type the word' }}</div>
      <div v-if="!locked" class="kb">
        <button v-for="k in keys" :key="k" type="button" lang="hy" class="key" @click="type(k)">{{ k }}</button>
        <button type="button" class="key wide" @click="type(' ')">Space</button>
        <button type="button" class="key wide" aria-label="Backspace" @click="back"><Icon name="chevron-left" :size="16"/></button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.aw { display: flex; flex-direction: column; align-items: center; gap: 10px; width: 100%; }
.padwrap { position: relative; width: min(100%, 420px); }
.pad { display: block; width: 100%; height: min(220px, 30vh); color: var(--text); background: var(--panel); border: 1px solid var(--line-2); border-radius: var(--radius); touch-action: none; user-select: none; -webkit-user-select: none; cursor: crosshair; }
.pad.guide { position: absolute; inset: 0; pointer-events: none; }
.pad.ink { position: relative; background: transparent; }
.clr { position: absolute; top: 6px; right: 6px; }
.typed { min-height: 46px; width: min(100%, 420px); display: flex; align-items: center; justify-content: center; font-size: 26px; border-bottom: 2px solid var(--accent); padding: 2px 8px; overflow-wrap: anywhere; }
.typed.empty { font-size: 14px; color: var(--faint); }
.kb { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; width: 100%; max-width: 440px; }
.key { min-width: 40px; height: 44px; padding: 0 8px; font: inherit; font-size: 20px; border-radius: var(--radius-sm); border: 1px solid var(--line-2); background: var(--panel); color: var(--text); cursor: pointer; touch-action: manipulation; display: inline-flex; align-items: center; justify-content: center; }
.key:active { background: var(--accent-soft); }
.key.wide { min-width: 84px; font-size: 14px; }
@media (max-width: 420px) { .key { min-width: 36px; padding: 0 4px; } }
</style>
