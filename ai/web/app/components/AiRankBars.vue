<script setup lang="ts">
// top 12 of the listed models on the Score or one index; fill is accent for installed models
const props = defineProps<{ rows: any[]; picks: string[] }>()
const emit = defineEmits<{ select: [id: string] }>()
const KEYS = ['reasoning', 'coding', 'knowledge', 'agents']
const key = ref('score')
const get = (r: any) => (key.value === 'score' ? r.score : key.value === 'arena' ? r.arena?.elo : r.indexes?.[key.value]?.v)
const top = computed(() => props.rows.filter(r => get(r) != null).sort((a, b) => get(b) - get(a)).slice(0, 12))
const go = ref(false)
let raf = 0
function replay() {
  cancelAnimationFrame(raf)
  go.value = false
  if (!import.meta.client) return
  raf = requestAnimationFrame(() => { raf = requestAnimationFrame(() => { go.value = true }) })
}
watch([key, () => top.value.map(r => r.id).join()], replay)
onMounted(replay)
onBeforeUnmount(() => cancelAnimationFrame(raf))
const pct = (v: number) => `${Math.round(v * 100)}%`
// Elo has no 0..1 scale: bars run from just under the lowest to the highest of the list
const lo = computed(() => Math.min(...top.value.map(get)) - 40)
const wid = (r: any) => (key.value === 'arena' ? `${Math.round(((get(r) - lo.value) / (Math.max(...top.value.map(get)) - lo.value || 1)) * 100)}%` : pct(get(r)))
const txt = (r: any) => (key.value === 'arena' ? String(get(r)) : pct(get(r)))
</script>

<template>
  <div class="rb">
    <div class="seg scroll-x nowrap">
      <button :class="{ on: key === 'score' }" @click="key = 'score'">{{ $t('ai.cmp.score') }}</button>
      <button :class="{ on: key === 'arena' }" @click="key = 'arena'">{{ $t('ai.cmp.arena') }}</button>
      <button v-for="k in KEYS" :key="k" :class="{ on: key === k }" @click="key = k">{{ $t(`ai.cmp.idx.${k}`) }}</button>
    </div>
    <p v-if="!top.length" class="empty-state">{{ $t('ai.cmp.noScores') }}</p>
    <div v-else class="list">
      <button v-for="(r, i) in top" :key="r.id" type="button" class="brw" :class="{ sel: picks.includes(r.id) }" @click="emit('select', r.id)">
        <span class="n">{{ r.name }}</span>
        <span class="trk"><span class="f" :class="{ inst: r.installed }" :style="{ width: go ? wid(r) : '0%', transitionDelay: `${i * 40}ms` }" /></span>
        <span class="v num">{{ txt(r) }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.rb { margin-bottom: 14px; }
.seg { max-width: 100%; margin-bottom: 10px; }
.list { display: grid; gap: 2px; }
.brw { display: grid; grid-template-columns: minmax(90px, 36%) 1fr 48px; align-items: center; gap: 8px; min-height: 30px; padding: 2px 6px; background: none; border: 0; border-radius: var(--radius-sm); color: var(--text); font: inherit; font-size: 13px; text-align: left; cursor: pointer; }
.brw:hover, .brw.sel { background: var(--accent-soft); }
.n { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.trk { height: 10px; background: var(--accent-soft); border-radius: 5px; overflow: hidden; }
.f { display: block; height: 100%; background: var(--track); border-radius: 5px; transition: width .6s cubic-bezier(.2, .7, .2, 1); }
.f.inst { background: var(--accent); }
.v { text-align: right; color: var(--muted); }
@media (prefers-reduced-motion: reduce) { .f { transition: none; } }
@media (max-width: 640px) { .brw { grid-template-columns: minmax(80px, 38%) 1fr 40px; font-size: 12px; } }
</style>
