<script setup lang="ts">
/** a category as a pill in its colour (colour = token name from the agent: accent, ok, warn, bad, claude, muted, faint, text) */
defineProps<{ name: string, color?: string }>()
</script>

<template>
  <span class="cat-pill" :style="{ '--c': `var(--${color || 'muted'})` }">{{ name }}</span>
</template>

<style scoped>
.cat-pill { display: inline-flex; align-items: center; padding: 1px 8px; border-radius: 999px; font-size: 11.5px; white-space: nowrap;
  color: var(--c); background: color-mix(in srgb, var(--c) 14%, transparent); }
</style>
