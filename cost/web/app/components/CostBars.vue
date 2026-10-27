<script setup lang="ts">
/** one stacked bar per day (viewBox scaled, no hover needed): tap a bar to pick the day, the page shows its detail.
 * `bars[i].parts` are values per series key in the order of `series`; `fmt` formats the y ticks and the total. */
export interface CostBar { day: string, parts: Record<string, number> }
const props = defineProps<{ bars: CostBar[], series: { key: string, label: string, color: string }[], fmt: (n: number) => string, height?: number }>()
const sel = defineModel<string | null>({ default: null })
const W = 600
const H = computed(() => props.height ?? 170)
const P = { t: 8, b: 4 }
const totals = computed(() => props.bars.map(b => Object.values(b.parts).reduce((a, v) => a + (v || 0), 0)))
const top = computed(() => {
  const m = Math.max(...totals.value, 0)
  if (m <= 0) return 1
  const step = 10 ** Math.floor(Math.log10(m)) / 2
  return Math.ceil(m / step) * step
})
const slot = computed(() => W / Math.max(props.bars.length, 1))
const bw = computed(() => Math.max(slot.value * 0.72, 1))
const y = (v: number) => P.t + (1 - v / top.value) * (H.value - P.t - P.b)
const rects = computed(() => props.bars.map((b, i) => {
  let acc = 0
  const x = i * slot.value + (slot.value - bw.value) / 2
  return props.series.map((s) => {
    const v = b.parts[s.key] || 0
    const r = { key: s.key, color: s.color, x, w: bw.value, y: y(acc + v), h: Math.max(y(acc) - y(acc + v), v > 0 ? 1 : 0) }
    acc += v
    return r
  })
}))
const ticks = computed(() => [0.5, 1].map(f => f * top.value))
const dm = (d: string) => fmtDate(d + 'T12:00', { day: 'numeric', month: 'short' })
function pick(e: MouseEvent) {
  const r = (e.currentTarget as SVGElement).getBoundingClientRect()
  const i = Math.min(props.bars.length - 1, Math.max(0, Math.floor(((e.clientX - r.left) / r.width) * props.bars.length)))
  const d = props.bars[i]?.day
  if (d) sel.value = sel.value === d ? null : d
}
</script>

<template>
  <div class="cb">
    <div class="box">
      <svg :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="none" class="chart" :style="{ height: H + 'px' }" @click="pick">
        <line v-for="t in ticks" :key="t" x1="0" :x2="W" :y1="y(t)" :y2="y(t)" class="grid" />
        <line x1="0" :x2="W" :y1="H - P.b" :y2="H - P.b" class="grid" />
        <rect v-if="sel && bars.findIndex(b => b.day === sel) >= 0" :x="bars.findIndex(b => b.day === sel) * slot" y="0" :width="slot" :height="H" class="selbg" />
        <g v-for="(g, i) in rects" :key="bars[i]!.day" :class="{ dim: sel && sel !== bars[i]!.day }">
          <rect v-for="r in g" :key="r.key" :x="r.x" :y="r.y" :width="r.w" :height="r.h" :fill="r.color" />
        </g>
      </svg>
      <span v-for="t in ticks" :key="'l' + t" class="yl" :style="{ top: y(t) + 'px' }">{{ fmt(t) }}</span>
    </div>
    <div v-if="bars.length" class="ax small"><span>{{ dm(bars[0]!.day) }}</span><span>{{ dm(bars[Math.floor(bars.length / 2)]!.day) }}</span><span>{{ dm(bars.at(-1)!.day) }}</span></div>
    <div class="legend small"><span v-for="s in series" :key="s.key"><i class="sw" :style="{ background: s.color }" />{{ s.label }}</span></div>
  </div>
</template>

<style scoped>
.box { position: relative; }
.chart { width: 100%; display: block; touch-action: pan-y; cursor: pointer; }
.grid { stroke: var(--line); stroke-width: 1; vector-effect: non-scaling-stroke; }
.selbg { fill: var(--accent-soft); }
.dim { opacity: 0.45; }
.yl { position: absolute; right: 2px; transform: translateY(-100%); font-size: 10.5px; color: var(--faint); pointer-events: none; background: color-mix(in srgb, var(--panel) 70%, transparent); padding: 0 3px; border-radius: 3px; }
.ax { display: flex; justify-content: space-between; color: var(--faint); margin-top: 4px; }
.legend { display: flex; gap: 6px 14px; flex-wrap: wrap; color: var(--muted); margin-top: 8px; }
.sw { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 5px; vertical-align: -1px; }
</style>
