<script setup lang="ts">
/** one card: everything on it and how it is doing (recognition + write) */
const props = defineProps<{ k: string }>()
const emit = defineEmits<{ close: [], changed: [] }>()
const x = ref<any>(null)
const error = ref('')
async function load() {
  try { x.value = await $fetch('/api/armenian/card', { query: { k: props.k } }); error.value = '' } catch (e: any) { error.value = e?.data?.statusMessage || e?.message }
}
watch(() => props.k, load, { immediate: true })

const { armed, arm } = useArm()
async function forget() {
  if (!arm('forget')) return
  try { await $fetch('/api/armenian/action', { method: 'POST', body: { action: 'forget', k: props.k } }); await load(); emit('changed') } catch (e: any) { error.value = e?.data?.statusMessage || e?.message }
}
const STATE: Record<string, string> = { learning: 'Learning', relearning: 'Relearning', review: 'Review' }
const fmt = (t: number) => new Date(t * 1000).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
const ivl = (d: number) => (d < 30 ? `${d} d` : d < 365 ? `${(d / 30).toFixed(1)} mo` : `${(d / 365).toFixed(1)} y`)
const RATE = ['', 'Again', 'Hard', 'Good', 'Easy']
</script>

<template>
  <div class="scrim" @click.self="emit('close')">
    <div class="sheet">
      <button type="button" class="btn ghost icon x" aria-label="close" @click="emit('close')"><Icon name="x" :size="16"/></button>
      <p v-if="error" class="errbox">{{ error }}</p>
      <template v-if="x">
        <div lang="hy" class="glyph" :class="{ sm: x.t === 'w' }">{{ x.hy }}</div>
        <div class="pills">
          <span class="pill">{{ groupName(x.g) }}</span>
          <span v-if="x.card" class="pill accent">{{ STATE[x.card.state] }}</span>
          <span v-else class="pill">New</span>
        </div>
        <ArmenianFace :c="x" />
        <div v-if="x.card" class="card small muted">
          <span>Interval {{ x.card.state === 'review' ? ivl(x.card.ivl) : '–' }}</span>
          <span>Due {{ fmt(x.card.due) }}</span>
          <span>Ease {{ x.card.ease }}%</span>
          <span>{{ x.card.reps }} reviews · {{ x.card.lapses }} lapses</span>
        </div>
        <div v-if="x.write" class="card small muted">
          <span>Writing: {{ x.write.state === 'review' ? `every ${ivl(x.write.ivl)}` : STATE[x.write.state] }}</span>
          <span>{{ x.write.reps }} written · {{ x.write.lapses }} lapses</span>
        </div>
        <div v-if="x.history.length" class="hist faint small">
          <span v-for="(h, i) in x.history" :key="i" :class="{ bad: h.rating === 1 }" :title="fmt(h.ts)">{{ h.w ? 'w ' : '' }}{{ RATE[h.rating] }}</span>
        </div>
        <div v-if="x.card" class="foot">
          <button type="button" class="btn sm" :class="{ sure: armed === 'forget' }" @click="forget">{{ armed === 'forget' ? 'Sure?' : 'Reset to new' }}</button>
        </div>
      </template>
      <Skeleton v-else-if="!error" kind="lines" :n="3" />
    </div>
  </div>
</template>

<style scoped>
.scrim { position: fixed; inset: 0; z-index: 60; background: rgba(0, 0, 0, .55); display: flex; justify-content: center; align-items: flex-start; padding: 5vh 16px; overflow-y: auto; }
.sheet { position: relative; width: 100%; max-width: 560px; background: var(--panel); border: 1px solid var(--line-2); border-radius: 16px; padding: 18px 20px 14px; display: flex; flex-direction: column; gap: 12px; }
.x { position: absolute; top: 8px; right: 8px; }
.gl { display: flex; align-items: center; justify-content: center; gap: 8px; }
.glyph { font-size: 90px; line-height: 1.15; text-align: center; overflow-wrap: anywhere; }
.glyph.sm { font-size: 48px; }
.pills { display: flex; gap: 6px; justify-content: center; flex-wrap: wrap; }
.card { display: flex; flex-wrap: wrap; gap: 4px 14px; justify-content: center; }
.hist { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; }
.foot { display: flex; justify-content: flex-end; border-top: 1px solid var(--line); padding-top: 10px; }
@media (max-width: 640px) { .scrim { padding: 12px 8px; } .sheet { padding: 16px 14px 12px; } }
</style>
