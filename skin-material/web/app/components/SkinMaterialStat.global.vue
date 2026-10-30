<script setup lang="ts">
/** Stat: label medium over a title-large value, tinted by tone */
withDefaults(defineProps<{ label?: string, value?: string | number, tone?: string }>(), { label: '', value: '' })
</script>

<template>
  <div class="stat m3-stat"><span class="lbl">{{ label }}</span><b :class="tone">{{ value }}</b></div>
</template>

<style scoped>
.m3-stat { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.lbl { font-size: 12px; font-weight: 500; letter-spacing: .5px; color: var(--muted); }
b { font-size: 22px; font-weight: 400; line-height: 28px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text); }
b.ok { color: var(--ok); } b.warn { color: var(--warn); } b.bad { color: var(--bad); }
</style>
