<script setup lang="ts">
// what holds the GPU's memory right now: Ollama's loaded models and every other GPU process, and what still fits
const data = ref<any>(null)
const error = ref('')
let timer: any

async function load() {
  try {
    data.value = await $fetch<any>('/api/ai/vram')
    error.value = ''
  } catch (e: any) { error.value = e?.data?.statusMessage || e?.message || 'error' }
  timer = setTimeout(load, 8000)
}
onMounted(load)
onBeforeUnmount(() => clearTimeout(timer))

const gb = (mb: number) => (mb / 1024).toFixed(1)
const pct = (mb: number) => (data.value ? Math.min(100, (mb / data.value.total_mb) * 100) : 0)
const room = computed(() => (data.value ? Math.max(data.value.free_mb - data.value.reserve_mb, 0) : 0))
</script>

<template>
  <div class="grid">
    <div v-if="error" class="errbox">{{ error }}</div>
    <Panel :title="$t('ai.vramTitle')" :sub="data ? $t('ai.vramUsed', { used: gb(data.used_mb), total: gb(data.total_mb), free: gb(data.free_mb) }) : ''">
      <Skeleton v-if="!data" kind="rows" :n="4" />
      <template v-else>
        <div class="tr"><span class="fill" :style="{ width: pct(data.used_mb) + '%' }" /></div>
        <p class="small">{{ $t('ai.vramFits', { n: gb(room) }) }}</p>
        <p class="faint small">{{ $t('ai.vramReserve', { n: gb(data.reserve_mb) }) }}</p>
        <div class="sec">{{ $t('ai.vramProcs') }}</div>
        <div v-for="u in data.users" :key="u.label" class="vrow"><span class="grow">{{ u.label }}</span><span class="num muted">{{ gb(u.mb) }} GB</span></div>
        <div class="sec">{{ $t('ai.vramOllama') }}</div>
        <p v-if="!data.loaded.length" class="muted small">{{ $t('ai.nothingLoaded') }}</p>
        <div v-for="m in data.loaded" :key="m.name" class="vrow">
          <span class="grow mono">{{ m.name }} <span v-if="m.warm" class="pill accent">{{ $t('ai.warm') }}</span></span>
          <span class="num muted small">{{ $t('ai.inVram', { n: m.size ? Math.round(m.vram / m.size * 100) : 0 }) }}</span>
          <span class="num muted">{{ bytes(m.size) }}</span>
        </div>
      </template>
    </Panel>
  </div>
</template>

<style scoped>
.tr { height: 10px; border-radius: 999px; background: var(--track); overflow: hidden; margin: 4px 0 10px; }
.fill { display: block; height: 100%; background: var(--accent); }
.vrow { display: flex; align-items: center; gap: 8px; padding: 6px 0; flex-wrap: wrap; }
.grow { flex: 1 1 140px; min-width: 0; }
</style>
