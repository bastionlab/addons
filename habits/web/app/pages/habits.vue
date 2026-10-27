<script setup lang="ts">
useHead({ title: 'Habits · Bastion' })
// the tracker is its own offline-first app in CT 204 (bastionlab/habits); the dash only frames it
const { ts } = useDashConfig()
const src = computed(() => ts('habits') && `${ts('habits')}/`)

// the viewer's design (Designs add-on, if installed) goes into the frame: the app asks with bastion:ready
const frame = ref<HTMLIFrameElement | null>(null)
function sendLook() {
  if (!frame.value?.contentWindow || !src.value) return
  frame.value.contentWindow.postMessage({ type: 'bastion:look', look: (window as any).__bastionLook ?? null }, new URL(src.value).origin)
}
const onMsg = (e: MessageEvent) => { if (e.source === frame.value?.contentWindow && e.data?.type === 'bastion:ready') sendLook() }
onMounted(() => { addEventListener('message', onMsg); addEventListener('bastion:look', sendLook) })
onUnmounted(() => { removeEventListener('message', onMsg); removeEventListener('bastion:look', sendLook) })
</script>

<template>
  <iframe v-if="src" ref="frame" class="habits" :src="src" title="Habits" />
</template>

<style scoped>
.habits { display: block; width: 100%; max-width: 640px; margin: 0 auto; height: calc(100dvh - 48px); margin-bottom: -36px; border: 0; background: var(--bg); }
@media (max-width: 640px) { .habits { height: calc(100dvh - 24px - var(--tabbar, 0px)); margin-bottom: -16px; } }
</style>
