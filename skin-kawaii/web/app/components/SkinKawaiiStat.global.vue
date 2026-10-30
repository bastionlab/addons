<script setup lang="ts">
/** Stat: a tiny label over a value in a soft pastel pill */
defineProps<{ label?: string, value?: string | number, tone?: string }>()
</script>

<template>
  <div class="stat"><span class="lbl">{{ label }}</span><b :class="tone">{{ value }}</b></div>
</template>

<style scoped>
.stat { display: flex; flex-direction: column; align-items: flex-start; gap: 3px; min-width: 0; }
.lbl { font-size: 11.5px; font-weight: 700; color: var(--faint); }
b { max-width: 100%; padding: 2px 10px; border-radius: 999px; font-size: 15px; font-weight: 800; background: color-mix(in srgb, var(--accent) 9%, var(--panel)); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
b.ok { color: var(--ok); background: color-mix(in srgb, var(--ok) 12%, var(--panel)); }
b.warn { color: var(--warn); background: color-mix(in srgb, var(--warn) 13%, var(--panel)); }
b.bad { color: var(--bad); background: color-mix(in srgb, var(--bad) 12%, var(--panel)); }
</style>
