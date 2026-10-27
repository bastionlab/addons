<script setup lang="ts">
import { isDoneOn, isoDay, isScheduled, weekdayOf, type HabitRow } from '../utils/habits'
/** Habits' card on the home page: how many of today's habits are done */
const { t } = useI18n()
const d = ref<{ habits: HabitRow[], checks: Record<string, string[]> } | null>(null)
onMounted(async () => { try { d.value = await $fetch('/api/habits') } catch {} })
const sub = computed(() => {
  if (!d.value) return t('habits.home.sub')
  const now = new Date(), key = isoDay(now), wd = weekdayOf(now)
  const ck = Object.fromEntries(Object.entries(d.value.checks).map(([k, v]) => [k, new Set(v)]))
  const due = d.value.habits.filter(h => isScheduled(h, wd))
  if (!due.length) return t(d.value.habits.length ? 'habits.nothingTodayShort' : 'habits.home.sub')
  return t('habits.home.today', { n: due.filter(h => isDoneOn(ck, h.id, key)).length, total: due.length })
})
</script>

<template>
  <TopicCard to="/habits" icon="check" :name="t('habits.title')" :sub="sub" />
</template>
