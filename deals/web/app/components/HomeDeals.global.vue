<script setup lang="ts">
/** Deals' card on the home page */
const { data: d, refresh } = useDeals()
onMounted(refresh) // changes in the background: fresh on every visit
const fresh = computed(() => (d.value?.feed ?? []).filter((i: any) => Date.now() / 1000 - (i.posted_at ?? i.first_seen_at ?? 0) < 86400).length)
const chips = computed(() => d.value
  ? [
      { text: `${d.value.status?.enabled ?? 0} searches` },
      ...(fresh.value ? [{ text: `${fresh.value} new`, tone: 'accent' }] : []),
    ]
  : [])
// large card: the newest finds
const eur = (c: number | null | undefined) => (c == null ? '' : `${Math.round(c / 100)} €`)
const more = computed(() => (d.value?.feed ?? []).slice(0, 4).map((i: any) => ({ text: i.title, sub: eur(i.price_cents) })))
</script>

<template>
  <TopicCard to="/deals" icon="deals" name="Deals" sub="Kleinanzeigen hunter" :chips="chips" :more="more" />
</template>
