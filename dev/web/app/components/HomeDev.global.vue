<script setup lang="ts">
/** Dev's card on the home page */
const { data: boxes, refresh } = useProjects()
onMounted(() => { if (!boxes.value) refresh() })
const projects = computed(() => (boxes.value ?? []).flatMap(b => b.projects ?? []))
const previews = computed(() => projects.value.filter((p: any) => p.running).length)
const claudes = computed(() => projects.value.filter((p: any) => p.cc?.running).length)
const chips = computed(() => boxes.value
  ? [
      { text: `${projects.value.length} projects` },
      ...(previews.value ? [{ text: `${previews.value} running`, tone: 'ok' }] : []),
      ...(claudes.value ? [{ text: `${claudes.value} Claude`, tone: 'accent' }] : []),
    ]
  : [])
// large card: what is running right now
const more = computed(() => projects.value.filter((p: any) => p.running || p.cc?.running).slice(0, 4).map((p: any) => ({ text: p.name, sub: [p.running && 'preview', p.cc?.running && 'Claude'].filter(Boolean).join(' · '), tone: 'ok' })))
</script>

<template>
  <TopicCard to="/dev" icon="dev" name="Dev" sub="Projects & terminals" :chips="chips" :more="more" />
</template>
