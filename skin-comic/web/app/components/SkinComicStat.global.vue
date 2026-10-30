<script setup lang="ts">
/** Stat: tiny caption label, big inked figure */
defineProps<{ label?: string, value?: string | number, tone?: string }>()
</script>

<template>
  <div class="cstat"><span class="lbl">{{ label }}</span><b :class="tone">{{ value }}</b></div>
</template>

<style scoped>
.cstat { display: flex; flex-direction: column; align-items: flex-start; gap: 3px; min-width: 0; }
.lbl { padding: 1px 6px; font-size: 10.5px; font-weight: 900; text-transform: uppercase; letter-spacing: .05em; color: var(--line-2); background: var(--comic-yellow); border: 2px solid var(--line-2); }
b { max-width: 100%; font-size: 21px; font-weight: 900; font-style: italic; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
b.ok { color: var(--ok); } b.warn { color: var(--warn); } b.bad { color: var(--bad); }
</style>
