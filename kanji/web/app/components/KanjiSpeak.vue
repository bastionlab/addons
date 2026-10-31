<script setup lang="ts">
/** speaker button: plays the clip, shows loading / playing / error */
const props = withDefaults(defineProps<{ text: string, size?: number }>(), { size: 16 })
const st = computed(() => kjSpeakState(props.text))
</script>

<template>
  <button type="button" class="btn ghost icon spk" :class="st" :aria-label="st === 'err' ? 'Sound unavailable' : 'Play sound'" @click.stop="kjSpeak(text)">
    <Icon :name="st === 'load' ? 'refresh-cw' : st === 'err' ? 'triangle-alert' : 'volume-2'" :size="size" />
  </button>
</template>

<style scoped>
.spk { min-width: 36px; min-height: 36px; }
.spk.play { color: var(--accent); }
.spk.err { color: var(--bad); }
.spk.load :deep(svg) { animation: spkspin 1s linear infinite; }
@keyframes spkspin { to { transform: rotate(360deg) } }
@media (pointer: coarse) { .spk { min-width: 44px; min-height: 44px; } }
</style>
