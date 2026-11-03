<script setup lang="ts">
// radar over the four indexes where at least two of the picked models have a value; a missing index is a gap
const props = defineProps<{ models: any[] }>()
const { t } = useI18n()
const label = (b: { key: string; label: string }) => b.label
const COLORS = ['var(--accent)', 'var(--ok)', 'var(--warn)']
const C = 170, R = 100
const hidden = ref<string[]>([])
const axes = computed(() => ['reasoning', 'coding', 'knowledge', 'agents'].map(key => ({ key, label: t(`ai.cmp.idx.${key}`) })).filter(b => props.models.filter(m => m.indexes?.[b.key] != null).length >= 2))
const ang = (i: number) => -Math.PI / 2 + (2 * Math.PI * i) / Math.max(axes.value.length, 1)
const pt = (i: number, v: number, k = 1) => ({ x: C + Math.cos(ang(i)) * R * v * k, y: C + Math.sin(ang(i)) * R * v * k })
const grow = ref(0)
let raf = 0
function play() {
  cancelAnimationFrame(raf)
  if (!import.meta.client || window.matchMedia('(prefers-reduced-motion: reduce)').matches) { grow.value = 1; return }
  const t0 = performance.now()
  grow.value = 0
  const step = (now: number) => {
    const p = Math.min(1, (now - t0) / 600)
    grow.value = 1 - (1 - p) ** 3
    if (p < 1) raf = requestAnimationFrame(step)
  }
  raf = requestAnimationFrame(step)
}
watch(() => [props.models.map(m => m.id).join(), axes.value.map(a => a.key).join()], play)
onMounted(play)
onBeforeUnmount(() => cancelAnimationFrame(raf))
const series = computed(() => props.models.map((m, i) => {
  const vals = axes.value.map(a => m.indexes?.[a.key]?.v as number | null | undefined)
  const pts = vals.map((v, j) => (v == null ? null : pt(j, Math.min(1, Math.max(0, v)), grow.value)))
  const full = pts.every(p => p)
  // runs of consecutive present points; a missing axis breaks the line
  const runs: { x: number; y: number }[][] = []
  let cur: { x: number; y: number }[] = []
  for (const p of pts) { if (p) cur.push(p); else if (cur.length) { runs.push(cur); cur = [] } }
  if (cur.length) runs.push(cur)
  const d = runs.map(r => r.map((p, k) => `${k ? 'L' : 'M'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')).join(' ') + (full ? ' Z' : '')
  const missing = axes.value.filter((_, j) => vals[j] == null).map(label)
  return { m, color: COLORS[i % 3], pts, d, full, missing, off: hidden.value.includes(m.id) }
}))
const labelPos = (i: number) => {
  const p = pt(i, 1.14)
  const c = Math.cos(ang(i))
  return { x: p.x, y: p.y + 4, a: Math.abs(c) < 0.2 ? 'middle' : c > 0 ? 'start' : 'end' }
}
const ringPath = (f: number) => axes.value.map((_, i) => { const p = pt(i, f); return `${i ? 'L' : 'M'}${p.x.toFixed(1)} ${p.y.toFixed(1)}` }).join(' ') + ' Z'
function flip(id: string) { hidden.value = hidden.value.includes(id) ? hidden.value.filter(x => x !== id) : [...hidden.value, id] }
</script>

<template>
  <div class="radar">
    <p v-if="axes.length < 3" class="empty-state">{{ $t('ai.cmp.radarFew') }}</p>
    <template v-else>
      <svg viewBox="0 0 340 340" class="rsvg" role="img" :aria-label="$t('ai.cmp.view.radar')">
        <path v-for="f in [0.25, 0.5, 0.75, 1]" :key="f" :d="ringPath(f)" class="ring" />
        <line v-for="(_, i) in axes" :key="i" :x1="C" :y1="C" :x2="pt(i, 1).x" :y2="pt(i, 1).y" class="spoke" />
        <text v-for="(a, i) in axes" :key="a.key" :x="labelPos(i).x" :y="labelPos(i).y" :text-anchor="labelPos(i).a" class="lab">{{ label(a) }}</text>
        <template v-for="s in series" :key="s.m.id">
          <g v-if="!s.off">
            <path :d="s.d" :stroke="s.color" :fill="s.full ? s.color : 'none'" :fill-opacity="s.full ? 0.14 : 0" class="poly" />
            <template v-for="(p, i) in s.pts" :key="i"><circle v-if="p" :cx="p.x" :cy="p.y" r="3" :fill="s.color" /></template>
          </g>
        </template>
      </svg>
      <div class="legend">
        <button v-for="s in series" :key="s.m.id" type="button" class="chip lg" :class="{ on: !s.off }" :aria-pressed="!s.off" @click="flip(s.m.id)">
          <span class="sw" :style="{ background: s.color }" />{{ s.m.name }}
        </button>
      </div>
      <p v-for="s in series.filter(x => x.missing.length)" :key="s.m.id" class="faint small note">{{ s.m.name }}: {{ $t('ai.cmp.na') }} ({{ s.missing.join(', ') }})</p>
    </template>
  </div>
</template>

<style scoped>
.radar { margin-bottom: 14px; }
.rsvg { display: block; width: 100%; max-width: 340px; aspect-ratio: 1; margin: 0 auto; }
.ring { fill: none; stroke: var(--line); stroke-width: 1; }
.spoke { stroke: var(--line); stroke-width: 1; }
.lab { fill: var(--muted); font-size: 11px; }
.poly { stroke-width: 2; stroke-linejoin: round; }
.legend { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; margin-top: 8px; }
.lg { display: inline-flex; align-items: center; gap: 6px; }
.lg:not(.on) { opacity: .5; }
.sw { width: 10px; height: 10px; border-radius: 50%; flex: none; }
.note { text-align: center; margin: 6px 0 0; }
@media (pointer: coarse) { .lg { min-height: 32px; } }
</style>
