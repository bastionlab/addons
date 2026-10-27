<script setup lang="ts">
import { habitStats, isDoneOn, isoDay, isScheduled, midnight, weekdayOf, type HabitChecks, type HabitRow } from '../utils/habits'
/** Today tab: greeting + progress ring, the perfect-day streak with this week, and today's habits to tick off */
const props = defineProps<{ habits: HabitRow[], checks: HabitChecks, now: Date, perfect: number, sound: boolean }>()
const emit = defineEmits<{ toggle: [id: string, row: HTMLElement | null], sound: [] }>()
const { t } = useI18n()

const today = computed(() => midnight(props.now))
const list = computed(() => {
  const key = isoDay(today.value), wd = weekdayOf(today.value)
  return props.habits.filter(h => isScheduled(h, wd))
    .map(h => ({ h, done: isDoneOn(props.checks, h.id, key), s: habitStats(h, props.checks, today.value) }))
    .sort((a, b) => Number(a.done) - Number(b.done))
})
const n = computed(() => list.value.filter(x => x.done).length)
const all = computed(() => list.value.length > 0 && n.value === list.value.length)
const p = computed(() => (list.value.length ? n.value / list.value.length : 0))
const RING = 2 * Math.PI * 26
const hr = computed(() => props.now.getHours())
const greet = computed(() => t(hr.value < 5 ? 'habits.greet.late' : hr.value < 12 ? 'habits.greet.morning' : hr.value < 18 ? 'habits.greet.afternoon' : 'habits.greet.evening'))
const sub = computed(() => {
  const total = list.value.length
  if (!total) return ''
  if (all.value) return t('habits.sub.perfect')
  if (total - n.value === 1) return t('habits.sub.oneMore')
  if (props.perfect && hr.value >= 17) return t('habits.sub.keep', { n: n.value, total, streak: props.perfect })
  return t('habits.sub.progress', { n: n.value, total })
})
</script>

<template>
  <div class="today">
    <div class="hero" :class="{ all }">
      <div class="htxt">
        <span class="greet">{{ greet }}</span>
        <b>{{ fmtDate(now, { weekday: 'long', day: 'numeric', month: 'long' }) }}</b>
        <span class="sub">{{ sub }}</span>
      </div>
      <button class="btn ghost icon snd" :aria-label="t(sound ? 'habits.soundOn' : 'habits.soundOff')" @click="emit('sound')"><Icon :name="sound ? 'volume-2' : 'ban'" :size="16"/></button>
      <div v-if="list.length" class="ring">
        <svg viewBox="0 0 60 60">
          <circle class="trk" cx="30" cy="30" r="26" />
          <circle class="val" cx="30" cy="30" r="26" :stroke-dasharray="RING" :style="{ strokeDashoffset: RING * (1 - p) }" />
        </svg>
        <span><Icon v-if="all" name="check" :size="22" /><template v-else>{{ Math.round(p * 100) }}<small>%</small></template></span>
      </div>
    </div>

    <div v-if="habits.length" class="pstreak" :class="{ all }">
      <span class="pn" :class="{ zero: !perfect }" :title="t('habits.perfectInARow')"><HabitsFlame :size="22" /><b>{{ perfect }}</b><small>{{ t('habits.dayStreak') }}</small></span>
      <HabitsWeek :habits="habits" :checks="checks" :today="today" />
    </div>

    <div v-if="!list.length" class="empty-state">
      <div class="eico"><Icon :name="habits.length ? 'target' : 'sparkles'" :size="32"/></div>
      {{ t(habits.length ? 'habits.nothingToday' : 'habits.noneYet') }}
    </div>
    <TransitionGroup v-else name="hl" tag="div" class="list">
      <button
        v-for="({ h, done, s }, i) in list" :key="h.id" class="row" :class="{ done }" :style="{ '--i': i }"
        @click="emit('toggle', h.id, ($event.currentTarget as HTMLElement))"
      >
        <span class="box"><Icon name="check" :size="14" /></span>
        <span class="t"><span class="tx">{{ h.title }}</span></span>
        <HabitsChip :n="s.streak" :best="s.best" :weekly="h.freq === 'weekly'" />
      </button>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.hero { display: flex; align-items: center; gap: 10px; margin: 0 2px 16px; }
.htxt { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.greet { color: var(--faint); font-size: 13px; }
.hero b { font-size: 22px; font-weight: 650; letter-spacing: -.02em; margin: 1px 0 2px; }
.sub { color: var(--muted); font-size: 13px; }
.hero.all .sub { color: var(--ok); }
.snd { flex: none; font-size: 15px; opacity: .7; }
.ring { position: relative; width: 64px; height: 64px; flex: none; }
.ring > svg { width: 100%; height: 100%; transform: rotate(-90deg); overflow: visible; }
.ring circle { fill: none; stroke-width: 6; }
.ring .trk { stroke: var(--track); }
.ring .val { stroke: var(--accent); stroke-linecap: round; transition: stroke-dashoffset .8s cubic-bezier(.3, 1.4, .5, 1), stroke .4s; }
.hero.all .ring .val { stroke: var(--ok); }
.ring span { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-weight: 650; font-size: 15px; font-variant-numeric: tabular-nums; }
.ring small { font-size: 10px; color: var(--muted); font-weight: 500; margin-left: 1px; }
.hero.all .ring span { color: var(--ok); }

.pstreak { display: flex; align-items: center; gap: 12px; margin: 0 0 16px; padding: 10px 12px; background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); transition: border-color .4s; }
.pstreak.all { border-color: var(--warn); }
.pn { flex: none; display: flex; align-items: center; gap: 4px; color: var(--warn); }
.pn svg { animation: flicker 2.4s ease-in-out infinite; transform-origin: 50% 90%; }
.pn b { font-size: 20px; font-weight: 700; font-variant-numeric: tabular-nums; }
.pn small { color: var(--muted); font-size: 11px; line-height: 1.1; width: 34px; }
.pn.zero { color: var(--faint); }
.pn.zero svg { animation: none; }

.list { display: flex; flex-direction: column; gap: 8px; position: relative; }
.row { position: relative; display: flex; align-items: center; gap: 13px; width: 100%; text-align: left; padding: 14px 15px; font: inherit; color: var(--text);
  background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); cursor: pointer; transition: background .25s, border-color .25s, transform .12s; }
.row:hover { border-color: var(--line-2); }
.row:active { transform: scale(.985); }
.row.done { background: color-mix(in srgb, var(--panel) 60%, var(--bg)); }
.box { flex: none; width: 24px; height: 24px; border-radius: 50%; border: 2px solid var(--line-2); display: grid; place-items: center; color: var(--bg); transition: background .25s, border-color .25s; }
.box svg { opacity: 0; }
.row:hover .box { border-color: var(--muted); }
.done .box { background: var(--ok); border-color: var(--ok); }
.done .box svg { opacity: 1; }
.done .box { animation: pop .45s cubic-bezier(.3, 1.4, .5, 1); }
.t { flex: 1; min-width: 0; overflow-wrap: anywhere; }
.tx { background: linear-gradient(currentColor, currentColor) 0 58% / 0 1.5px no-repeat; transition: color .3s, background-size .4s; }
.done .tx { color: var(--faint); background-size: 100% 1.5px; }
.done :deep(.hchip) { opacity: .65; }
.hl-move { transition: transform .48s cubic-bezier(.2, .8, .2, 1); }
.hl-enter-active { animation: rise .45s cubic-bezier(.2, .8, .2, 1) both; animation-delay: calc(var(--i, 0) * 45ms); }
.eico { font-size: 34px; margin-bottom: 8px; }
@keyframes pop { 0% { transform: scale(.55) } 60% { transform: scale(1.22) } 100% { transform: scale(1) } }
@keyframes rise { from { opacity: 0; transform: translateY(10px) } }
@keyframes flicker { 0%, 100% { transform: scale(1) rotate(0) } 25% { transform: scale(1.08, .94) rotate(-4deg) } 50% { transform: scale(.95, 1.07) rotate(3deg) } 75% { transform: scale(1.05) rotate(-2deg) } }
@media (pointer: coarse) { .snd { min-width: 34px; } }
@media (prefers-reduced-motion: reduce) { .row, .box, .tx, .ring .val, .hl-move, .hl-enter-active, .pn svg { animation: none !important; transition: none !important; } }
</style>
