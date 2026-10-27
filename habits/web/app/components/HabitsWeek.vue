<script setup lang="ts">
import { addDays, dayState, midnight, weekdayOf, type HabitChecks, type HabitRow } from '../utils/habits'
/** Mon–Sun of this week: flame = perfect day, red = missed, dashed ring = today still open */
const props = defineProps<{ habits: HabitRow[], checks: HabitChecks, today: Date, big?: boolean }>()
const { t } = useI18n()
const days = computed(() => {
  const tdy = midnight(props.today), mon = addDays(tdy, -weekdayOf(tdy))
  return Array.from({ length: 7 }, (_, i) => {
    const d = addDays(mon, i), s = d > tdy ? undefined : dayState(props.habits, props.checks, d), now = +d === +tdy
    const cls = s === true ? 'win' : s === false ? (now ? 'open' : 'miss') : d > tdy ? 'fut' : 'rest'
    return { i, cls, now, name: t(`habits.dow.${i}`).slice(0, 2) }
  })
})
</script>

<template>
  <div class="week" :class="{ big }">
    <span v-for="d in days" :key="d.i" class="wk" :class="[d.cls, { now: d.now }]" :style="{ '--i': d.i }">
      <i><HabitsFlame v-if="d.cls === 'win'" :size="big ? 18 : 13" /></i>{{ d.name }}
    </span>
  </div>
</template>

<style scoped>
.week { flex: 1; min-width: 0; display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
.wk { display: flex; flex-direction: column; align-items: center; gap: 3px; font-size: 10px; color: var(--faint); }
.wk i { width: 24px; height: 24px; border-radius: 50%; display: grid; place-items: center; background: var(--panel-2); border: 2px solid transparent; }
.wk.win i { background: var(--warn); color: var(--bg); }
.wk.miss i { background: var(--bad-soft); }
.wk.open i { border-color: var(--warn); border-style: dashed; animation: spin 8s linear infinite; }
.wk.fut i { background: none; border: 2px solid var(--line); }
.wk.rest i { background: none; border: 2px dotted var(--line-2); }
.wk.now { color: var(--text); font-weight: 600; }
.week.big { gap: 6px; }
.week.big .wk i { width: 34px; height: 34px; }
.week.big .wk { animation: pop-in .4s cubic-bezier(.3, 1.4, .5, 1) both; animation-delay: calc(var(--i) * 60ms + 650ms); }
.week.big .wk.now.win i { animation: stamp .7s 1.15s cubic-bezier(.3, 1.4, .5, 1) both; box-shadow: 0 0 0 4px var(--warn-soft); }
@keyframes spin { to { transform: rotate(360deg) } }
@keyframes pop-in { from { opacity: 0; transform: scale(.5) } }
@keyframes stamp { 0% { transform: scale(2.2); opacity: 0 } 60% { transform: scale(.9); opacity: 1 } 100% { transform: scale(1) } }
@media (prefers-reduced-motion: reduce) { .wk, .wk i { animation: none !important; } }
</style>
