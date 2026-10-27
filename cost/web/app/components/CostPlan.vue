<script setup lang="ts">
/** plan window usage over time: two lines (5 h window, week) on a 0 to 100 % axis; shares given as 0-1 or 0-100 */
const props = defineProps<{ points: { t: number, five_h: number, week: number }[] }>()
const { t } = useI18n()
const W = 600, H = 120
const pct = computed(() => (Math.max(...props.points.flatMap(p => [p.five_h, p.week]), 0) <= 1.5 ? 100 : 1))
const ms = (v: number) => (v < 1e12 ? v * 1000 : v)
const tr = computed(() => ({ a: ms(props.points[0]?.t ?? 0), b: Math.max(ms(props.points.at(-1)?.t ?? 1), ms(props.points[0]?.t ?? 0) + 1) }))
const x = (v: number) => ((ms(v) - tr.value.a) / (tr.value.b - tr.value.a)) * W
const y = (v: number) => 6 + (1 - Math.min(Math.max(v * pct.value, 0), 100) / 100) * (H - 12)
const line = (k: 'five_h' | 'week') => props.points.map((p, i) => `${i ? 'L' : 'M'}${x(p.t).toFixed(1)},${y(p[k]).toFixed(1)}`).join('')
const last = computed(() => props.points.at(-1))
const p100 = (v: number) => `${Math.round(v * pct.value)}%`
</script>

<template>
  <div>
    <div class="legend small">
      <span><i class="sw a" />{{ t('cost.fiveH') }} <b v-if="last">{{ p100(last.five_h) }}</b></span>
      <span><i class="sw b" />{{ t('cost.week') }} <b v-if="last">{{ p100(last.week) }}</b></span>
    </div>
    <svg v-if="points.length > 1" :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="none" class="chart" :style="{ height: H + 'px' }">
      <line v-for="g in [0, 50, 100]" :key="g" x1="0" :x2="W" :y1="y(g / pct)" :y2="y(g / pct)" class="grid" />
      <path :d="line('week')" class="ln b" />
      <path :d="line('five_h')" class="ln a" />
    </svg>
    <div v-else class="faint small pad">{{ t('cost.noPlan') }}</div>
  </div>
</template>

<style scoped>
.chart { width: 100%; display: block; }
.grid { stroke: var(--line); stroke-width: 1; vector-effect: non-scaling-stroke; }
.ln { fill: none; stroke-width: 2; vector-effect: non-scaling-stroke; stroke-linejoin: round; }
.ln.a { stroke: var(--accent); }
.ln.b { stroke: var(--muted); }
.legend { display: flex; gap: 14px; flex-wrap: wrap; color: var(--muted); margin-bottom: 6px; }
.legend b { color: var(--text); font-weight: 600; margin-left: 4px; }
.sw { display: inline-block; width: 14px; height: 2px; vertical-align: middle; margin-right: 5px; }
.sw.a { background: var(--accent); } .sw.b { background: var(--muted); }
.pad { padding: 20px 0; }
</style>
