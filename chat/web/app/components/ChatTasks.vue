<script setup lang="ts">
// scheduled chat tasks (server/utils/chatTasks.ts): list, add / edit, on-off, run now, delete
const emit = defineEmits<{ close: [], open: [string] }>()
const { t: tr } = useI18n()
const tasks = ref<any[]>([])
const err = ref('')
const loading = ref(true)
async function load() {
  try { tasks.value = (await $fetch<any>('/api/chat-tasks')).tasks } catch (e: any) { err.value = e?.data?.statusMessage || e?.message } finally { loading.value = false }
}
onMounted(load)

const DAYS = [1, 2, 3, 4, 5, 6, 0]
const dayName = (d: number) => new Date(2026, 0, 4 + d).toLocaleDateString('en-GB', { weekday: 'short' }) // 2026-01-04 = Sunday
const blank = () => ({ title: '', prompt: '', time: '08:00', days: [] as number[], every: 0, model: 'sonnet', effort: 'medium', auto: false, team: true, quiet: true, on: true })
const form = ref<any>(null)
const mode = computed({ get: () => (form.value?.every ? 'every' : 'time'), set: v => { form.value.every = v === 'every' ? (form.value.every || 6) : 0 } })
const edit = (t?: any) => { err.value = ''; form.value = t ? { ...blank(), ...t, every: t.every ?? 0 } : blank() }
const toggleDay = (d: number) => { const s = form.value.days as number[]; s.includes(d) ? s.splice(s.indexOf(d), 1) : s.push(d) }

async function call(body: any) {
  err.value = ''
  try { await $fetch('/api/chat-tasks', { method: 'POST', body }); await load(); return true } catch (e: any) { err.value = e?.data?.statusMessage || e?.message; return false }
}
async function saveForm() { if (await call({ op: 'put', task: form.value })) form.value = null }
const flip = (t: any) => call({ op: 'put', task: { ...t, on: !t.on } })
const run = async (t: any) => { if (await call({ op: 'run', id: t.id })) emit('open', t.chat) }
const { armed, arm } = useArm() // tap twice to delete
const del = (t: any) => arm(t.id) && call({ op: 'del', id: t.id })

const when = (t: any) => t.every ? tr('chat.everyH', { n: t.every }) : `${t.days.length ? DAYS.filter(d => t.days.includes(d)).map(dayName).join(' ') : tr('chat.daily')} ${t.time}`
const modelName = (id: string) => CLAUDE_MODELS.find(m => m.id === id)?.label ?? id
const at = (ms?: number) => ms ? new Date(ms).toLocaleString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'
</script>

<template>
  <div class="sheet">
    <div class="sh">
      <b><Icon name="alarm-clock" :size="18"/> {{ $t('chat.tasks') }}</b>
      <button v-if="!form" type="button" class="btn sm primary" @click="edit()">+ {{ $t('chat.taskNew') }}</button>
      <button type="button" class="btn ghost sm x" :title="$t('chat.close')" @click="emit('close')" :aria-label="$t('chat.close')"><Icon name="x" :size="16"/></button>
    </div>
    <div v-if="err" class="errbox small">{{ err }}</div>
    <form v-if="form" class="form" @submit.prevent="saveForm">
      <input v-model="form.title" :placeholder="$t('chat.taskTitle')" maxlength="60">
      <textarea v-model="form.prompt" rows="4" :placeholder="$t('chat.taskPrompt')" required />
      <div class="seg">
        <button type="button" :class="{ on: mode === 'time' }" @click="mode = 'time'">{{ $t('chat.atTime') }}</button>
        <button type="button" :class="{ on: mode === 'every' }" @click="mode = 'every'">{{ $t('chat.everyHours') }}</button>
      </div>
      <div v-if="mode === 'time'" class="row">
        <input v-model="form.time" type="time" required>
        <span class="days">
          <button v-for="d in DAYS" :key="d" type="button" class="chip" :class="{ on: form.days.includes(d) }" @click="toggleDay(d)">{{ dayName(d) }}</button>
        </span>
      </div>
      <div v-else class="row"><input v-model.number="form.every" type="number" min="1" max="168" class="num"> <span class="muted small">{{ $t('chat.hours') }}</span></div>
      <div class="row">
        <select v-model="form.model"><option v-for="m in CLAUDE_MODELS" :key="m.id" :value="m.id">{{ m.label }}</option></select>
        <select v-model="form.effort"><option v-for="e in CLAUDE_EFFORTS" :key="e" :value="e">{{ e }}</option></select>
      </div>
      <label class="tg"><input v-model="form.quiet" type="checkbox"> {{ $t('chat.taskQuiet') }}</label>
      <label class="tg"><input v-model="form.team" type="checkbox"> {{ $t('chat.taskTeam') }}</label>
      <label class="tg warn"><input v-model="form.auto" type="checkbox"> {{ $t('chat.taskAuto') }}</label>
      <div class="row">
        <button class="btn primary sm">{{ $t('common.save') }}</button>
        <button type="button" class="btn ghost sm" @click="form = null">{{ $t('common.cancel') }}</button>
      </div>
    </form>
    <Skeleton v-else-if="loading" kind="rows" />
    <div v-else-if="!tasks.length" class="muted small empty">{{ $t('chat.noTasks') }}</div>
    <div v-for="t in form ? [] : tasks" :key="t.id" class="task" :class="{ off: !t.on }">
      <div class="tt">
        <b>{{ t.title }}</b>
        <span class="small muted">{{ when(t) }} · {{ modelName(t.model) }}<template v-if="t.auto"> · <Icon name="zap" :size="12"/></template></span>
        <span class="small faint">{{ $t('chat.next') }} {{ t.on ? at(t.next) : '—' }}<template v-if="t.last"> · {{ $t('chat.lastRun') }} {{ at(t.last) }}</template></span>
        <span v-if="t.error" class="small bad">{{ t.error }}</span>
      </div>
      <div class="ta">
        <button type="button" class="btn ghost sm" @click="flip(t)">{{ t.on ? $t('chat.pause') : $t('chat.resume') }}</button>
        <button type="button" class="btn ghost sm" @click="run(t)"><Icon name="play" :size="14"/> {{ $t('chat.runNow') }}</button>
        <button type="button" class="btn ghost sm" @click="emit('open', t.chat)">{{ $t('chat.openChat') }}</button>
        <button type="button" class="btn ghost sm" @click="edit(t)"><Icon name="edit" :size="13" /></button>
        <button type="button" class="btn ghost sm bad" :class="{ sure: armed === t.id }" @click="del(t)"><template v-if="armed === t.id">Delete?</template><Icon v-else name="x" :size="16"/></button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sheet { display: flex; flex-direction: column; gap: 10px; }
.sh { display: flex; align-items: center; gap: 8px; }
.sh b { flex: 1; }
.form { display: flex; flex-direction: column; gap: 8px; }
.form textarea { resize: vertical; font: inherit; }
.row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.days { display: flex; flex-wrap: wrap; gap: 4px; }
.num { width: 80px; }
.tg { display: flex; align-items: center; gap: 6px; font-size: 13px; }
.tg.warn { color: var(--warn); }
.task { display: flex; flex-direction: column; gap: 6px; border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 10px 12px; }
.task.off { opacity: .6; }
.tt { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.ta { display: flex; flex-wrap: wrap; gap: 4px; }
.bad { color: var(--bad); }
.empty { padding: 8px 0; }
</style>
