<script setup lang="ts">
/** Stat as a ledger line: small-caps label over a serif value in the tone's ink */
withDefaults(defineProps<{ label?: string, value?: string | number, tone?: string }>(), { label: '', value: '' })
</script>

<template>
  <div class="stat gm-stat" :class="tone">
    <span class="lbl">{{ label }}</span><b>{{ value }}</b>
  </div>
</template>

<style scoped>
.gm-stat { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.lbl { font-size: 11px; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
b { font: 600 17px/1.3 Georgia, "Palatino Linotype", serif; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ok b { color: var(--ok); }
.warn b { color: var(--warn); }
.bad b { color: var(--bad); }
</style>
