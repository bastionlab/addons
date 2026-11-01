<script setup lang="ts">
/** a stat as a HUD readout: small uppercase label over a condensed number, a left edge lit by its tone */
withDefaults(defineProps<{ label?: string, value?: string | number, tone?: string }>(), { label: '', value: '', tone: '' })
</script>

<template>
  <div class="ro" :class="tone">
    <span class="lbl">{{ label }}</span>
    <b class="val">{{ value }}</b>
  </div>
</template>

<style scoped>
.ro { --tc: var(--line-2); display: flex; flex-direction: column; gap: 2px; min-width: 0; padding: 3px 8px; border-left: 2px solid var(--tc); }
.ro.ok { --tc: var(--ok); } .ro.warn { --tc: var(--warn); } .ro.bad { --tc: var(--bad); }
.lbl { font-size: 10.5px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.val { font: 700 18px/1.15 "Bahnschrift", "Arial Narrow", "Roboto Condensed", system-ui, sans-serif; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-variant-numeric: tabular-nums; }
.ok .val { color: var(--ok); } .warn .val { color: var(--warn); } .bad .val { color: var(--bad); }
</style>
