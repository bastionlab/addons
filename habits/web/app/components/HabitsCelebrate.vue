<script setup lang="ts">
import { MILESTONES, type HabitChecks, type HabitRow } from '../utils/habits'
import { burst, rain, sfx, vibrate } from '../utils/habitsFx'
/** the perfect-day screen: medal with the streak rolling up, stats, this week, confetti and a fanfare */
const props = defineProps<{ n: number, done: number, habits: HabitRow[], checks: HabitChecks, today: Date }>()
const emit = defineEmits<{ close: [] }>()
const { t } = useI18n()
const ms = MILESTONES.includes(props.n)
const cheer = t(`habits.cheer.${Math.floor(Math.random() * 7)}`)
const medal = ref<HTMLElement>()
const go = ref<HTMLElement>()
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches
onMounted(() => {
  go.value?.focus({ preventScroll: true })
  sfx('win'); vibrate([20, 70, 20, 70, 40])
  if (reduced()) return
  rain(ms ? 160 : 110)
  setTimeout(() => burst(medal.value, 40, 160), 350)
})
</script>

<template>
  <Teleport to="body">
    <div class="cele" role="dialog" aria-modal="true" @click.self="emit('close')">
      <div class="card">
        <div ref="medal" class="medal"><span class="glow" /><HabitsFlame :size="96" />
          <b class="num"><span class="old">{{ n - 1 }}</span><span class="new">{{ n }}</span></b></div>
        <h1>{{ ms ? t('habits.celebrate.milestone', { n }) : t('habits.celebrate.perfect') }}</h1>
        <p>{{ ms ? t('habits.celebrate.milestoneBody', { n }) : cheer }}</p>
        <div class="cstats">
          <div style="--i:0"><b>+{{ done * 10 + 50 }}</b><span>{{ t('habits.celebrate.xp') }}</span></div>
          <div style="--i:1"><b><HabitsFlame :size="16" />{{ n }}</b><span>{{ t('habits.dayStreak') }}</span></div>
          <div style="--i:2"><b>{{ done }}/{{ done }}</b><span>{{ t('habits.celebrate.habits') }}</span></div>
        </div>
        <HabitsWeek :habits="habits" :checks="checks" :today="today" big />
        <button ref="go" class="btn primary go" @click="emit('close')">{{ t('habits.celebrate.continue') }}</button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.cele { position: fixed; inset: 0; z-index: 190; display: grid; place-items: center; padding: 20px; overflow-y: auto;
  background: radial-gradient(circle at 50% 35%, var(--warn-soft), color-mix(in srgb, var(--bg) 92%, transparent) 60%); backdrop-filter: blur(6px); animation: fade .3s both; }
.card { width: 100%; max-width: 380px; text-align: center; }
.medal { position: relative; width: 150px; height: 150px; margin: 0 auto 6px; display: grid; place-items: center; color: var(--warn); animation: medal .9s cubic-bezier(.3, 1.4, .5, 1) both; }
.medal svg { animation: flicker 2.4s .9s ease-in-out infinite; transform-origin: 50% 90%; }
.glow { position: absolute; inset: -20px; border-radius: 50%; background: conic-gradient(from 0deg, transparent, var(--warn-soft), transparent 30%, var(--warn-soft) 50%, transparent 65%, var(--warn-soft) 80%, transparent);
  animation: spin 9s linear infinite; mask: radial-gradient(circle, #000 30%, transparent 70%); -webkit-mask: radial-gradient(circle, #000 30%, transparent 70%); }
.num { position: absolute; top: 72px; height: 34px; overflow: hidden; font-size: 28px; font-weight: 800; color: var(--bg); font-variant-numeric: tabular-nums; }
.num span { display: block; line-height: 34px; animation: roll .5s 1s cubic-bezier(.3, 1.4, .5, 1) both; }
h1 { margin: 0; font-size: 30px; font-weight: 800; letter-spacing: -.02em; color: var(--warn); animation: rise .5s .25s both; }
p { margin: 6px 0 20px; color: var(--muted); animation: rise .5s .35s both; }
.cstats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 18px; }
.cstats div { background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); padding: 10px 4px; animation: pop-in .4s cubic-bezier(.3, 1.4, .5, 1) both; animation-delay: calc(var(--i) * 90ms + 450ms); }
.cstats b { display: flex; align-items: center; justify-content: center; gap: 3px; font-size: 19px; font-weight: 750; font-variant-numeric: tabular-nums; }
.cstats div:first-child b, .cstats b svg { color: var(--warn); }
.cstats span { display: block; color: var(--faint); font-size: 11px; margin-top: 2px; }
.card :deep(.week) { margin: 4px 0 22px; }
.go { width: 100%; padding: 13px; font-size: 16px; border-radius: 14px; background: var(--ok); border-color: var(--ok); animation: rise .5s 1.1s both; }
@keyframes fade { from { opacity: 0 } }
@keyframes rise { from { opacity: 0; transform: translateY(10px) } }
@keyframes pop-in { from { opacity: 0; transform: scale(.5) } }
@keyframes medal { 0% { transform: scale(0) rotate(-25deg); opacity: 0 } 60% { transform: scale(1.15) rotate(6deg); opacity: 1 } 100% { transform: none } }
@keyframes roll { from { transform: translateY(0) } to { transform: translateY(-100%) } }
@keyframes spin { to { transform: rotate(360deg) } }
@keyframes flicker { 0%, 100% { transform: scale(1) rotate(0) } 25% { transform: scale(1.08, .94) rotate(-4deg) } 50% { transform: scale(.95, 1.07) rotate(3deg) } 75% { transform: scale(1.05) rotate(-2deg) } }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; } .num .old { display: none; } }
</style>
