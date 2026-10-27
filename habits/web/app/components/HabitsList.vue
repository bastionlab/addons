<script setup lang="ts">
import { habitStats, midnight, type HabitChecks, type HabitFreq, type HabitRow } from '../utils/habits'
/** Habits tab: the add / edit form and the list (tap a row for its streak + calendar, delete asks before deleting) */
const props = defineProps<{ habits: HabitRow[], checks: HabitChecks, now: Date, editing: HabitRow | null }>()
const emit = defineEmits<{ save: [h: { id?: string, title: string, freq: HabitFreq, days: number[] }], cancel: [], open: [id: string], remove: [id: string] }>()
const { t } = useI18n()

const blank = () => ({ title: '', freq: 'daily' as HabitFreq, days: [(props.now.getDay() + 6) % 7] })
const form = reactive(blank())
const input = ref<HTMLInputElement>()
watch(() => props.editing, (h) => {
  Object.assign(form, h ? { title: h.title, freq: h.freq, days: [...h.days] } : blank())
  if (h) nextTick(() => input.value?.focus({ preventScroll: true }))
}, { immediate: true })
const valid = computed(() => form.title.trim() && (form.freq === 'daily' || form.days.length))
function pickFreq(f: HabitFreq) {
  form.freq = f
  if (f === 'weekly') form.days = form.days.length ? form.days.slice(0, 1) : blank().days
}
function pickDay(i: number) {
  form.days = form.freq === 'weekly' ? [i] : form.days.includes(i) ? form.days.filter(x => x !== i) : [...form.days, i].sort()
}
function submit() {
  if (!valid.value) return
  emit('save', { id: props.editing?.id, title: form.title.trim(), freq: form.freq, days: form.freq === 'daily' ? [0, 1, 2, 3, 4, 5, 6] : [...form.days] })
  Object.assign(form, blank())
  nextTick(() => input.value?.focus({ preventScroll: true }))
}

function label(h: HabitRow) {
  if (h.freq === 'daily' || h.days.length === 7) return t('habits.everyDay')
  if (h.freq === 'weekly') return t('habits.every', { day: t(`habits.dow.${h.days[0]}`) })
  return h.days.map(d => t(`habits.dow.${d}`)).join(', ')
}
const rows = computed(() => props.habits.map(h => ({ h, s: habitStats(h, props.checks, midnight(props.now)) })))

// in-app confirm instead of window.confirm
const asking = ref<HabitRow | null>(null)
function yes() { if (asking.value) emit('remove', asking.value.id); asking.value = null }
</script>

<template>
  <div>
    <Panel :title="t(editing ? 'habits.editHabit' : 'habits.newHabit')" id="habits-form">
      <form class="f" @submit.prevent="submit">
        <input ref="input" v-model="form.title" type="text" :placeholder="t('habits.placeholder')" autocomplete="off" maxlength="120">
        <div class="seg">
          <button v-for="q in (['daily', 'weekly', 'days'] as const)" :key="q" type="button" :class="{ on: form.freq === q }" @click="pickFreq(q)">{{ t(`habits.freq.${q}`) }}</button>
        </div>
        <div v-if="form.freq !== 'daily'" class="wd">
          <button v-for="i in 7" :key="i" type="button" class="chip" :class="{ on: form.days.includes(i - 1) }" @click="pickDay(i - 1)">{{ t(`habits.dow.${i - 1}`) }}</button>
        </div>
        <div class="actions">
          <button v-if="editing" type="button" class="btn" @click="emit('cancel')">{{ t('habits.cancel') }}</button>
          <button class="btn primary" :disabled="!valid">{{ t(editing ? 'habits.save' : 'habits.add') }}</button>
        </div>
      </form>
    </Panel>

    <h3 v-if="rows.length" class="sec">{{ t('habits.count', rows.length) }}</h3>
    <div class="list">
      <div v-for="{ h, s } in rows" :key="h.id" class="row" :class="{ edit: editing?.id === h.id }" role="button" tabindex="0" @click="emit('open', h.id)" @keydown.enter="emit('open', h.id)">
        <span class="t">{{ h.title }}<span class="s">{{ label(h) }}<template v-if="s.rate !== null"> · {{ s.rate }}%</template></span></span>
        <HabitsChip :n="s.streak" :best="s.best" :weekly="h.freq === 'weekly'" />
        <button class="btn ghost sm x" :aria-label="t('habits.delete')" @click.stop="asking = h"><Icon name="x" :size="16"/></button>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="asking" class="scrim" @click.self="asking = null">
        <div class="ask" role="alertdialog">
          <b>{{ t('habits.deleteQ', { name: asking.title }) }}</b>
          <p class="muted small">{{ t('habits.deleteWarn') }}</p>
          <div class="actions">
            <button class="btn" @click="asking = null">{{ t('habits.cancel') }}</button>
            <button class="btn danger" @click="yes">{{ t('habits.delete') }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.f { display: flex; flex-direction: column; gap: 12px; }
input[type=text] { width: 100%; background: var(--bg); border: 1px solid var(--line-2); border-radius: var(--radius-sm); padding: 10px 12px; color: var(--text); font: inherit; outline: none; }
input[type=text]:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.seg { align-self: flex-start; max-width: 100%; }
.wd { display: flex; gap: 6px; flex-wrap: wrap; }
.wd .chip { flex: 1; min-width: 40px; justify-content: center; padding-inline: 0; }
.actions { display: flex; gap: 8px; justify-content: flex-end; }
.sec { margin: 18px 3px 9px; }
.list { display: flex; flex-direction: column; gap: 8px; }
.row { display: flex; align-items: center; gap: 10px; padding: 12px 8px 12px 15px; background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); cursor: pointer; transition: border-color .2s; }
.row:hover { border-color: var(--line-2); }
.row.edit { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.t { flex: 1; min-width: 0; overflow-wrap: anywhere; }
.s { display: block; margin-top: 2px; color: var(--faint); font-size: 12px; }
.x { color: var(--faint); }
.x:hover { color: var(--bad); }
.scrim { position: fixed; inset: 0; z-index: 150; display: grid; place-items: center; padding: 20px; background: color-mix(in srgb, var(--bg) 70%, transparent); backdrop-filter: blur(4px); }
.ask { width: 100%; max-width: 340px; background: var(--panel); border: 1px solid var(--line-2); border-radius: var(--radius); padding: 18px; display: flex; flex-direction: column; gap: 6px; overflow-wrap: anywhere; }
.ask p { margin: 0 0 10px; }
</style>
