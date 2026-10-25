<script setup lang="ts">
/** Flats' card on the home page */
const { data: d, refresh } = useFlats()
onMounted(refresh) // changes in the background: fresh on every visit
const fresh = computed(() => (d.value?.feed ?? []).filter((i: any) => Date.now() / 1000 - (i.posted_at ?? i.first_seen_at ?? 0) < 86400).length)
const chips = computed(() => d.value
  ? [
      { text: `${d.value.status?.enabled ?? 0} searches` },
      ...(fresh.value ? [{ text: `${fresh.value} new`, tone: 'accent' }] : []),
    ]
  : [])
// large card: the newest flats
const more = computed(() => (d.value?.feed ?? []).slice(0, 4).map((i: any) => ({ text: i.title, sub: [i.district, i.warm ? `${i.warm} €` : ''].filter(Boolean).join(' · ') })))
</script>

<template>
  <TopicCard to="/wohnungen" icon="key" name="Flats" sub="Flat hunter" :chips="chips" :more="more" />
</template>
