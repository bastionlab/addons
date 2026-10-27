<script setup lang="ts">
import { habitStats, isoDay, parseDay, isScheduled, midnight, weekdayOf, type HabitChecks, type HabitRow } from '../utils/habits'
/** one habit: streak, best, hit rate and a month calendar (tap a past day to mark / unmark it) */
const props = defineProps<{ habit: HabitRow, checks: HabitChecks, now: Date }>()
const emit = defineEmits<{ back: [], edit: [], day: [day: string, el: HTMLElement] }>()
const { t } = useI18n()

const today = computed(() => midnight(props.now))
const s = computed(() => habitStats(props.habit, props.checks, today.value))
const month = ref(new Date(today.value.getFullYear(), today.value.getMonth(), 1))
const atNow = computed(() => month.value.getFullYear() === today.value.getFullYear() && month.value.getMonth() === today.value.getMonth())
const shift = (n: number) => { month.value = new Date(month.value.getFullYear(), month.value.getMonth() + n, 1) }
const cells = computed(() => {
  const y = month.value.getFullYear(), m = month.value.getMonth(), len = new Date(y, m + 1, 0).getDate(), t0 = today.value
  const out: { blank?: true, n?: number, key?: string, cls?: string, fut?: boolean }[] = Array.from({ length: weekdayOf(month.value) }, () => ({ blank: true as const }))
  for (let i = 1; i <= len; i++) {
    const d = new Date(y, m, i), key = isoDay(d), due = isScheduled(props.habit, weekdayOf(d))
    const cls = d > t0 ? 'fut' : s.value.done.has(key) ? 'done' : +d === +t0 ? (due ? 'today' : 'off') : due && d >= s.value.start ? 'miss' : 'off'
    out.push({ n: i, key, cls, fut: d > t0 })
  }
  return out
})
const label = computed(() => {
  const h = props.habit
  if (h.freq === 'daily' || h.days.length === 7) return t('habits.everyDay')
  if (h.freq === 'weekly') return t('habits.every', { day: t(`habits.dow.${h.days[0]}`) })
  return h.days.map(d => t(`habits.dow.${d}`)).join(', ')
})
const dayTitle = (key: string) => fmtDate(parseDay(key), { weekday: 'short', day: 'numeric', month: 'short' })
</script>

<template>
  <div>
    <div class="dhead">
      <button class="btn" @click="emit('back')">‹ {{ t('habits.back') }}</button>
      <button class="btn" @click="emit('edit')"><Icon name="edit" :size="14" /> {{ t('habits.edit') }}</button>
    </div>
    <h2>{{ habit.title }}</h2>
    <div class="sub muted small">{{ label }}</div>
    <div class="stats">
      <div class="stat"><b class="fl"><HabitsFlame :size="16" />{{ s.streak }}</b><span>{{ t('habits.streak') }}</span></div>
      <div class="stat"><b>{{ s.best }}</b><span>{{ t('habits.best') }}</span></div>
      <div class="stat"><b>{{ s.rate === null ? '–' : s.rate + '%' }}</b><span>{{ t('habits.last30') }}</span></div>
      <div class="stat"><b>{{ s.total }}</b><span>{{ t('habits.doneTotal') }}</span></div>
    </div>
    <Panel :title="fmtDate(month, { month: 'long', year: 'numeric' })" id="habits-cal">
      <template #actions>
        <button class="btn ghost sm" :aria-label="t('habits.prevMonth')" @click="shift(-1)">‹</button>
        <button class="btn ghost sm" :aria-label="t('habits.nextMonth')" :disabled="atNow" @click="shift(1)">›</button>
      </template>
      <div class="grid">
        <span v-for="i in 7" :key="'w' + i" class="wh">{{ t(`habits.dow.${i - 1}`)[0] }}</span>
        <template v-for="(c, i) in cells" :key="i">
          <span v-if="c.blank" />
          <span v-else-if="c.fut" class="c fut">{{ c.n }}</span>
          <button v-else class="c" :class="c.cls" :aria-label="dayTitle(c.key!)" @click="emit('day', c.key!, $event.currentTarget as HTMLElement)">{{ c.n }}</button>
        </template>
      </div>
    </Panel>
  </div>
</template>

<style scoped>
.dhead { display: flex; justify-content: space-between; margin-bottom: 16px; }
h2 { margin: 0 2px; font-size: 22px; font-weight: 650; letter-spacing: -.02em; overflow-wrap: anywhere; }
.sub { margin: 2px 2px 16px; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 7px; margin-bottom: 14px; }
.stat { background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); padding: 11px 4px; text-align: center; min-width: 0; }
.stat b { display: flex; align-items: center; justify-content: center; gap: 4px; font-size: 20px; font-weight: 650; font-variant-numeric: tabular-nums; }
.stat b.fl { color: var(--warn); }
.stat span { display: block; color: var(--faint); font-size: 11px; margin-top: 2px; }
.grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; }
.wh { text-align: center; color: var(--faint); font-size: 11px; padding-bottom: 2px; }
.c { aspect-ratio: 1; display: grid; place-items: center; border-radius: 10px; border: 1px solid transparent; background: none; font: inherit; font-size: 13px; font-variant-numeric: tabular-nums; padding: 0; color: var(--muted); transition: background .25s, color .25s, border-color .2s; }
button.c { cursor: pointer; }
button.c:hover { border-color: var(--line-2); }
.c.done { background: var(--ok); color: var(--bg); font-weight: 650; }
.c.miss { background: var(--bad-soft); color: var(--bad); }
.c.today { border-color: var(--accent); color: var(--text); }
.c.off { color: var(--faint); }
.c.fut { color: var(--line-2); }
</style>
