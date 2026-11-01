<script setup lang="ts">
/** a stat as a neon readout: cyan label, glowing value */
withDefaults(defineProps<{ label?: string, value?: string | number, tone?: string }>(), { label: '', value: '' })
</script>

<template>
  <div class="ns" :class="tone"><span class="lbl">{{ label }}</span><b class="val">{{ value }}</b></div>
</template>

<style scoped>
.ns { --g: var(--accent); display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.ns.ok { --g: var(--ok); } .ns.warn { --g: var(--warn); } .ns.bad { --g: var(--bad); }
.lbl { font-size: 11px; text-transform: uppercase; letter-spacing: .12em; color: rgb(150 244 255); opacity: .85; }
.val { font: italic 700 18px/1.2 "Trebuchet MS", system-ui, sans-serif; color: var(--text); text-shadow: 0 0 6px var(--g), 0 0 14px color-mix(in srgb, var(--g) 60%, transparent); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
