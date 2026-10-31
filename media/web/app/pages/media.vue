<script setup lang="ts">
useHead({ title: 'Media · Bastion' })
const { data: m, error, pending, refresh } = useMedia()
usePoll(refresh, 8000)

const q = computed(() => m.value?.queues ?? {})
const { t } = useI18n()
const tab = usePageTab('downloads')
const tabs = computed(() => [
  { key: 'downloads', label: t('tabs.downloads'), badge: queue.value.length || undefined, tone: 'ok' as const },
  { key: 'library', label: t('tabs.library') },
  { key: 'apps', label: t('tabs.apps') },
])
const queue = computed(() => [...(q.value.movies ?? []), ...(q.value.series ?? []), ...(q.value.books ?? [])])
</script>

<template>
  <div>
    <AskPanel
      scope="media" placeholder="Ask about downloads, the VPN or the library…"
      :examples="['Is the VPN actually protecting me?', 'What is downloading right now?', 'How much space is the library using?', 'Is anything stuck?']"
      @refresh="refresh"
    />

    <PageTabs v-model="tab" :tabs="tabs" />
    <Skeleton v-if="!m && pending" kind="cards" :n="6" />
    <div v-else-if="error && !m" class="bad pad">Could not read the media stack: {{ error.statusMessage || error.message }}</div>

    <template v-if="m">
      <div v-if="tab === 'downloads'" class="grid cols-2">
        <VpnPanel :vpn="m.vpn" :torrents="m.torrents" />
        <QueuePanel id="q-all" title="Queue" :items="queue" empty="Nothing queued" />
        <WatchdogPanel :w="m.watchdog" />
      </div>
      <div v-else-if="tab === 'library'" class="grid cols-2">
        <LibraryPanel :library="m.library" :sizes="m.sizes" />
        <MediaRemove @removed="refresh" />
      </div>
      <ServicesPanel v-else-if="tab === 'apps'" :services="m.services ?? []" list />
    </template>
  </div>
</template>

<style scoped>
.pad { padding: 60px 0; text-align: center; }
.grid { align-items: start; }
</style>
