<script setup lang="ts">
useHead({ title: 'Models · pve' })
const { t } = useI18n()
const tab = usePageTab('cookbook')
const tabs = computed(() => ['cookbook', 'bench', 'jobs', 'vram', 'compare'].map(k => ({ key: k, label: t(`ai.tabs.${k}`) })))
</script>

<template>
  <div>
    <PageTabs v-model="tab" :tabs="tabs" />
    <AiCookbook v-if="tab === 'cookbook'" />
    <AiBench v-else-if="tab === 'bench'" />
    <AiJobs v-else-if="tab === 'jobs'" />
    <AiVram v-else-if="tab === 'vram'" />
    <AiCompare v-else />
  </div>
</template>
