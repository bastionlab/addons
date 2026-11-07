<script setup lang="ts">
// tokens/s + time to first token per installed model, run by the agent one model at a time and stored
const { toast } = useToast()
const data = ref<any>(null)
const error = ref('')
let timer: any

async function load() {
  try {
    data.value = await $fetch<any>('/api/ai/bench')
    error.value = ''
  } catch (e: any) { error.value = e?.data?.statusMessage || e?.message || 'error' }
  clearTimeout(timer)
  if (data.value?.running) timer = setTimeout(load, 4000)
}
onMounted(load)
onBeforeUnmount(() => clearTimeout(timer))

async function start() {
  try {
    await $fetch('/api/ai/bench/start', { method: 'POST' })
    if (data.value) data.value.running = true
    load()
  } catch (e: any) { toast(e?.data?.statusMessage || e?.message || 'failed', { tone: 'bad' }) }
}
const ms = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(1)} s` : `${n} ms`)
</script>

<template>
  <Panel :title="$t('ai.benchTitle')" :sub="data?.at ? $t('ai.benchAt', { when: fmtDate(data.at * 1000, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) }) : ''">
    <div v-if="error" class="errbox">{{ error }}</div>
    <Skeleton v-if="!data" kind="rows" :n="4" />
    <template v-else>
      <div class="bar">
        <button class="btn primary" :disabled="data.running" @click="start">{{ data.running ? $t('ai.benchRunning', { model: data.current }) : $t('ai.benchRun') }}</button>
        <span class="muted small">{{ $t('ai.benchWarn') }}</span>
      </div>
      <p v-if="data.error" class="errbox">{{ data.error }}</p>
      <div v-if="data.results?.length" class="scroll-x">
        <table>
          <thead><tr><th>{{ $t('ai.model') }}</th><th class="num">{{ $t('ai.tps') }}</th><th class="num">{{ $t('ai.ttft') }}</th><th class="num">{{ $t('ai.load') }}</th></tr></thead>
          <tbody>
            <tr v-for="r in data.results" :key="r.model">
              <td class="mono">{{ r.model }}</td>
              <template v-if="r.error"><td colspan="3"><span class="pill bad">{{ $t('ai.failed') }}</span></td></template>
              <template v-else>
                <td class="num">{{ r.tps }}</td><td class="num">{{ ms(r.ttft_ms) }}</td><td class="num">{{ ms(r.load_ms) }}</td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="empty-state">{{ $t('ai.benchNone') }}</p>
    </template>
  </Panel>
</template>

<style scoped>
.bar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 10px; }
</style>
