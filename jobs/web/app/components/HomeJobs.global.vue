<script setup lang="ts">
/** Jobs' card on the home page */
const { data: jobs, refresh } = useJobs()
onMounted(refresh) // changes in the background: fresh on every visit
const chips = computed(() => jobs.value
  ? [
      { text: `${jobs.value.status?.enabled ?? 0} searches` },
      ...(jobs.value.counts?.passed ? [{ text: `${jobs.value.counts.passed} matches`, tone: 'accent' }] : []),
    ]
  : [])
// large card: the best current matches
const more = computed(() => (jobs.value?.feed ?? []).slice(0, 4).map((i: any) => ({ text: i.title, sub: i.company ?? i.employer ?? '' })))
</script>

<template>
  <TopicCard to="/jobs" icon="briefcase" name="Jobs" sub="Job hunter" :chips="chips" :more="more" />
</template>
