<script setup lang="ts">
const { t } = useI18n()
useHead({ title: `${t('briefing.title')} · Bastion` })
const { data, error, refresh } = useFetch<any>('/api/briefing', { server: false, lazy: true })
const busy = ref(false)
const row = computed(() => data.value?.today ?? null)
const sections = computed(() => (row.value ? briefingSections(row.value.facts, row.value.matters, t) : []))
const unread = computed(() => (row.value ? briefingUnreadable(row.value.facts, t) : ''))
const waiting = computed(() => (data.value?.running || data.value?.nextAt <= Date.now() ? t('briefing.home.writing') : t('briefing.home.next', { time: data.value?.time })))
// a quiet day is only quiet when everything could be read
const incomplete = computed(() => !!unread.value)
const quiet = computed(() => !!row.value && !row.value.matters.length)

async function generate() {
  busy.value = true
  try {
    await $fetch('/api/briefing/run', { method: 'POST' })
    await refresh()
  } catch (e: any) {
    useToast().toast(t('briefing.failed', { why: e?.data?.statusMessage || e?.message || '' }), { tone: 'bad' })
  } finally { busy.value = false }
}
</script>

<template>
  <div class="bp">
    <div class="top">
      <h2 class="sec"><Icon name="alarm-clock" :size="18" /> {{ t('briefing.title') }}</h2>
      <button type="button" class="btn sm" :disabled="busy || !data" @click="generate">
        <Icon name="refresh-cw" :size="16" /> {{ busy ? t('briefing.generating') : t('briefing.generate') }}
      </button>
    </div>
    <div v-if="error && !data" class="errbox">{{ error.statusMessage || error.message }}</div>
    <Skeleton v-else-if="!data" kind="cards" :n="3" />
    <template v-else>
      <Panel v-if="!row" :title="t('briefing.today')">
        <p class="empty-state">{{ waiting }}</p>
      </Panel>
      <template v-else>
        <Panel :title="t('briefing.today')" :sub="ago(row.created)">
          <template #actions>
            <span class="pill" :class="[incomplete ? 'warn' : row.source === 'model' ? 'accent' : '']">{{ incomplete ? t('briefing.source.incomplete') : t(`briefing.source.${row.source}`) }}</span>
          </template>
          <p class="sum" :class="{ muted: quiet }">{{ quiet ? (unread || t('briefing.quiet')) : row.summary }}</p>
          <p v-if="unread && !quiet" class="small warn">{{ unread }}</p>
        </Panel>
        <div class="grid cols-2 secs">
          <Panel v-for="s in sections" :key="s.id" :title="s.title">
            <template #actions><span v-if="s.matters" class="pill accent">{{ t('briefing.attention') }}</span></template>
            <ul class="ls">
              <li v-for="(l, i) in s.lines" :key="i" :class="{ first: i === 0, [s.tone ?? '']: !!s.tone && i === 0 }">{{ l }}</li>
            </ul>
          </Panel>
        </div>
        <p class="faint small foot">{{ t('briefing.next', { time: data.time }) }}</p>
      </template>
    </template>
  </div>
</template>

<style scoped>
.bp { display: flex; flex-direction: column; gap: 14px; }
.top { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.top .sec { margin: 0; display: flex; align-items: center; gap: 8px; }
.sum { font-size: 16px; line-height: 1.45; margin: 0; overflow-wrap: anywhere; }
.ls { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 4px; }
.ls li { font-size: 13px; color: var(--muted); overflow-wrap: anywhere; white-space: pre-wrap; }
.ls li.first { color: var(--text); font-size: 14px; }
.ls li.warn { color: var(--warn); }
.ls li.bad { color: var(--bad); }
.warn { color: var(--warn); }
.foot { margin: 0; }
@media (pointer: coarse) { .top .btn { min-height: 36px; } }
</style>
