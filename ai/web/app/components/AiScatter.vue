<script setup lang="ts">
// score vs size: x = parameters in billions (log scale), y = Score
const props = defineProps<{ rows: any[]; picks: string[] }>()
const W = 360, H = 260, L = 34, Rr = 14, T = 12, B = 28
const TICKS = [1, 3, 9, 30, 100, 300, 1000]
const X = (p: number) => L + (Math.log10(Math.min(1000, Math.max(1, p))) / 3) * (W - L - Rr)
const Y = (s: number) => T + (1 - Math.min(1, Math.max(0, s))) * (H - T - B)
const pts = computed(() => {
  const all = props.rows.filter(r => r.score != null && r.params_b != null && r.params_b > 0)
  return [...all.filter(r => !r.installed), ...all.filter(r => r.installed)].map((r, i, a) => ({ r, x: X(r.params_b), y: Y(r.score), d: Math.round((i / Math.max(a.length, 1)) * 300) }))
})
const sel = ref<string | null>(null)
const cur = computed(() => pts.value.find(p => p.r.id === sel.value))
const root = ref<HTMLElement | null>(null)
function away(e: Event) { if (!(e.target as Element)?.closest?.('[data-pt]')) sel.value = null }
onMounted(() => document.addEventListener('pointerdown', away))
onBeforeUnmount(() => document.removeEventListener('pointerdown', away))
const short = (s: string) => (s.length > 16 ? `${s.slice(0, 15)}.` : s)
const showLab = (p: any) => p.r.installed || props.picks.includes(p.r.id)
</script>

<template>
  <div ref="root" class="sc">
    <p v-if="!pts.length" class="empty-state">{{ $t('ai.cmp.noScores') }}</p>
    <div v-else class="wrap-sc">
      <svg :viewBox="`0 0 ${W} ${H}`" class="ssvg" role="img" :aria-label="$t('ai.cmp.view.scatter')">
        <g v-for="s in [0, 0.25, 0.5, 0.75, 1]" :key="s">
          <line :x1="L" :x2="W - Rr" :y1="Y(s)" :y2="Y(s)" class="gl" />
          <text :x="L - 5" :y="Y(s) + 4" text-anchor="end" class="tk">{{ Math.round(s * 100) }}%</text>
        </g>
        <g v-for="t in TICKS" :key="t">
          <line :x1="X(t)" :x2="X(t)" :y1="T" :y2="H - B" class="gl" />
          <text :x="X(t)" :y="H - B + 14" text-anchor="middle" class="tk">{{ t }}B</text>
        </g>
        <template v-for="p in pts" :key="p.r.id">
          <circle v-if="picks.includes(p.r.id)" :cx="p.x" :cy="p.y" :r="p.r.installed ? 9 : 7" class="ring" />
          <circle :cx="p.x" :cy="p.y" :r="p.r.installed ? 5 : 2.5" :class="['dot', p.r.installed ? 'inst' : 'oth']" :style="{ animationDelay: `${p.d}ms` }" />
          <text v-if="showLab(p)" :x="p.x + (p.x > W * 0.7 ? -8 : 8)" :y="p.y + 3" :text-anchor="p.x > W * 0.7 ? 'end' : 'start'" class="pl">{{ short(p.r.name) }}</text>
          <circle :cx="p.x" :cy="p.y" r="11" class="hit" data-pt @click="sel = p.r.id" />
        </template>
      </svg>
      <div v-if="cur" class="tip" :style="{ left: `${(cur.x / W) * 100}%`, top: `${(cur.y / H) * 100}%` }" :class="{ flip: cur.x > W * 0.6 }">
        <div class="nm">{{ cur.r.name }}</div>
        <div class="muted small">{{ $t('ai.cmp.score') }} {{ Math.round(cur.r.score * 100) }}%, {{ cur.r.params_b }}B</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sc { margin-bottom: 14px; }
.wrap-sc { position: relative; max-width: 560px; margin: 0 auto; }
.ssvg { display: block; width: 100%; height: auto; }
.gl { stroke: var(--line); stroke-width: 1; }
.tk { fill: var(--faint); font-size: 9px; }
.pl { fill: var(--text); font-size: 9px; pointer-events: none; }
.dot { transform-box: fill-box; transform-origin: center; animation: pop .2s ease-out both; }
.dot.inst { fill: var(--accent); }
.dot.oth { fill: var(--faint); }
.ring { fill: none; stroke: var(--text); stroke-width: 1.5; }
.hit { fill: transparent; cursor: pointer; }
@keyframes pop { from { opacity: 0; transform: scale(.2); } to { opacity: 1; transform: scale(1); } }
.tip { position: absolute; z-index: 5; transform: translate(10px, -110%); background: var(--panel); border: 1px solid var(--line-2); border-radius: var(--radius-sm); padding: 6px 10px; font-size: 13px; pointer-events: none; white-space: nowrap; box-shadow: 0 8px 24px rgba(0, 0, 0, .35); }
.tip.flip { transform: translate(calc(-100% - 10px), -110%); }
@media (prefers-reduced-motion: reduce) { .dot { animation: none; } }
</style>
