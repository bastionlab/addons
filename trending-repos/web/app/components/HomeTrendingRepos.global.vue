<script setup lang="ts">
const { data } = useFetch<{ top: { repo: string }[], n: number }>('/api/trending-repos/home', { server: false, lazy: true })
const chips = computed(() => (data.value?.top ?? []).map(r => ({ text: r.repo.split('/')[1] ?? r.repo })))
const sub = computed(() => (data.value?.n ? `${data.value.n} new repos for you` : 'Nothing new yet'))
</script>

<template>
  <TopicCard to="/trending-repos" icon="flame" name="Trending repos" :sub="sub" :chips="chips" />
</template>
