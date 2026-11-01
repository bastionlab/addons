<script setup lang="ts">
/** Stat: small caption, Fluent-weight value, a thin accent tick on the left */
defineProps<{ label?: string, value?: string | number, tone?: string }>()
</script>

<template>
  <div class="stat" :class="tone"><span class="lbl">{{ label }}</span><b>{{ value }}</b></div>
</template>

<style scoped>
.stat { display: flex; flex-direction: column; gap: 1px; min-width: 0; padding-left: 9px; border-left: 2px solid color-mix(in srgb, var(--accent) 55%, transparent); }
.lbl { font-size: 11.5px; color: var(--faint); }
b { font-size: 17px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ok { border-left-color: var(--ok); } .ok b { color: var(--ok); }
.warn { border-left-color: var(--warn); } .warn b { color: var(--warn); }
.bad { border-left-color: var(--bad); } .bad b { color: var(--bad); }
</style>
