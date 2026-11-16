<script setup lang="ts">
const { t } = useI18n()
useHead({ title: `${t('alertwatch.title')} · Bastion` })
const { data, error, refresh } = useFetch<any>('/api/alertwatch', { server: false, lazy: true })
let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => { timer = setInterval(() => refresh(), 60_000) })
onUnmounted(() => clearInterval(timer))

const busy = ref('')
async function investigate(key: string) {
  busy.value = key
  try {
    await $fetch('/api/alertwatch/run', { method: 'POST', body: { key } })
    await refresh()
  } catch (e: any) {
    useToast().toast(t('alertwatch.failed', { why: errText(e, '') }), { tone: 'bad' })
  } finally { busy.value = '' }
}
const when = (ts: number) => fmtDate(ts, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
const canExec = (e: any) => !!e.run?.done && !e.run.allok && !e.run.executed && !!data.value?.chat
/** what is shown under the message: Claude's line, or that it is still looking */
const note = (e: any) => {
  if (!e.run) return e.closed == null ? t('alertwatch.investigating') : ''
  if (!e.run.done) return t('alertwatch.investigating')
  return e.run.allok ? t('alertwatch.cleared', { why: e.run.cause || '' }) : e.run.cause || ''
}
</script>

<template>
  <div class="aw">
    <div class="top">
      <h2 class="sec"><Icon name="siren" :size="18" /> {{ t('alertwatch.title') }}</h2>
    </div>
    <div v-if="error && !data" class="errbox">{{ errText(error, t('alertwatch.error')) }}</div>
    <Skeleton v-else-if="!data" kind="rows" :n="4" />
    <template v-else>
      <Panel :title="t('alertwatch.open')">
        <p v-if="!data.open.length" class="empty-state">{{ t('alertwatch.quiet') }}</p>
        <ul v-else class="ls">
          <li v-for="e in data.open" :key="e.key + e.at" class="row">
            <span class="dot st" :class="e.run?.done ? 'bad' : 'warn'" />
            <div class="main">
              <span class="msg">{{ alertPlain(e.msg) }}</span>
              <span class="muted small">{{ when(e.at) }}</span>
              <span v-if="note(e)" class="cause small" :class="{ muted: !e.run?.done }">{{ note(e) }}</span>
            </div>
            <div class="acts">
              <NuxtLink v-if="data.chat && e.run" :to="'/chat?c=' + data.chat" class="btn sm">{{ t('alertwatch.openChat') }}</NuxtLink>
              <button v-if="canExec(e)" type="button" class="btn sm primary" @click="alertwatchExecute(data.chat, e.run.turn)">{{ t('alertwatch.execute') }}</button>
              <button v-if="!e.run?.done" type="button" class="btn sm" :disabled="busy === e.key" @click="investigate(e.key)">{{ t('alertwatch.investigate') }}</button>
            </div>
          </li>
        </ul>
      </Panel>
      <Panel :title="t('alertwatch.history')">
        <p v-if="!data.log.length" class="empty-state">{{ t('alertwatch.quiet') }}</p>
        <ul v-else class="ls">
          <li v-for="e in data.log" :key="e.key + e.at" class="row">
            <span class="dot st" :class="e.closed == null ? (e.run?.done ? 'bad' : 'warn') : 'ok'" />
            <div class="main">
              <span class="msg">{{ alertPlain(e.msg) }}</span>
              <span class="muted small">{{ when(e.at) }}<template v-if="e.closed != null"> · {{ t('alertwatch.closed') }} {{ when(e.closed) }}</template></span>
              <span v-if="note(e)" class="cause small" :class="{ muted: !e.run?.done }">{{ note(e) }}</span>
            </div>
            <div class="acts">
              <NuxtLink v-if="data.chat && e.run" :to="'/chat?c=' + data.chat" class="btn sm">{{ t('alertwatch.openChat') }}</NuxtLink>
              <span v-if="e.run?.executed" class="pill ok">{{ t('alertwatch.executed') }}</span>
              <button v-else-if="e.closed == null && canExec(e)" type="button" class="btn sm primary" @click="alertwatchExecute(data.chat, e.run.turn)">{{ t('alertwatch.execute') }}</button>
            </div>
          </li>
        </ul>
      </Panel>
      <p v-if="data.checked" class="faint small foot">{{ t('alertwatch.lastCheck', { time: when(data.checked) }) }}</p>
    </template>
  </div>
</template>

<style scoped>
.aw { display: flex; flex-direction: column; gap: 14px; }
.top { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.top .sec { margin: 0; display: flex; align-items: center; gap: 8px; }
.ls { list-style: none; margin: 0; padding: 0; }
.row { display: flex; align-items: flex-start; gap: 10px; padding: 10px 0; border-top: 1px solid var(--line); }
.row:first-child { border-top: 0; padding-top: 2px; }
.st { flex: none; margin-top: 6px; }
.main { display: flex; flex-direction: column; gap: 2px; min-width: 0; flex: 1; }
.msg { overflow-wrap: anywhere; }
.cause { overflow-wrap: anywhere; }
.acts { display: flex; flex-wrap: wrap; justify-content: flex-end; align-items: center; gap: 6px; flex: none; }
.foot { margin: 0; }
/* phone: the buttons drop under the text */
@media (max-width: 640px) {
  .row { flex-wrap: wrap; }
  .main { flex-basis: calc(100% - 24px); }
  .acts { flex-basis: 100%; justify-content: flex-start; padding-left: 20px; }
}
@media (pointer: coarse) { .acts .btn { min-height: 32px; } }
</style>
