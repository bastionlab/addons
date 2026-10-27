<script setup lang="ts">
const { t } = useI18n()
const { data } = useFetch<CostSummary>('/api/cost/summary?days=31', { server: false, lazy: true })
const tot = computed(() => data.value ? costTotals(data.value, costMonthDays(data.value)) : null)
const chips = computed(() => tot.value ? [
  { text: fmtMoney(tot.value.power + tot.value.eur, 0) },
  { text: `${costUsd(tot.value.usd, 0)} Claude` },
  { text: fmtMoney(tot.value.power, 0) + ' ⚡' },
] : [])
</script>

<template>
  <TopicCard to="/cost" icon="layers" :name="t('cost.title')" :sub="t('cost.homeSub')" :chips="chips" />
</template>
