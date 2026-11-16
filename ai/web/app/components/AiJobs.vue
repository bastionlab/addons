<script setup lang="ts">
// one model per job; "" = the warm model. The server falls back to warm unless the chosen model is already loaded
const { optimistic } = useToast()
const { t } = useI18n()
const data = ref<any>(null)
const models = ref<any[]>([])
const error = ref('')

async function load() {
  try {
    const [j, m] = await Promise.all([$fetch<any>('/api/ai/jobs'), $fetch<any[]>('/api/ai/models')])
    data.value = j
    models.value = m.filter(x => !x.uncensored)
    error.value = ''
  } catch (e: any) { error.value = e?.data?.statusMessage || e?.message || 'error' }
}
onMounted(load)

function set(job: string, model: string) {
  const before = data.value.jobs[job]
  optimistic(() => (data.value.jobs[job] = model), () => (data.value.jobs[job] = before),
    () => $fetch('/api/ai/jobs', { method: 'POST', body: { job, model } }), t('ai.jobSaved'))
}
</script>

<template>
  <Panel :title="$t('ai.jobsTitle')" :sub="$t('ai.jobsNote')">
    <div v-if="error" class="errbox">{{ error }}</div>
    <Skeleton v-if="!data" kind="rows" :n="6" />
    <div v-else>
      <div v-for="k in data.keys" :key="k" class="jrow">
        <span class="grow">{{ $t(`ai.job.${k}`) }}</span>
        <select :value="data.jobs[k]" @change="set(k, ($event.target as HTMLSelectElement).value)">
          <option value="">{{ $t('ai.warmDefault') }}</option>
          <option v-for="m in models" :key="m.name" :value="m.name">{{ m.name }}</option>
          <option v-if="data.jobs[k] && !models.some(m => m.name === data.jobs[k])" :value="data.jobs[k]">{{ data.jobs[k] }}</option>
        </select>
      </div>
    </div>
  </Panel>
</template>

<style scoped>
.jrow { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-top: 1px solid var(--line); flex-wrap: wrap; }
.jrow:first-child { border-top: 0; }
.grow { flex: 1 1 160px; }
.jrow select { flex: 1 1 180px; min-width: 0; max-width: 100%; }
</style>
