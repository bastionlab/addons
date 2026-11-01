<script setup lang="ts">
/** Stat as a sunken field with its label above */
withDefaults(defineProps<{ label?: string, value?: string | number, tone?: string }>(), { label: '', value: '' })
</script>

<template>
  <div class="stat"><span class="lbl">{{ label }}</span><b class="fld" :class="tone">{{ value }}</b></div>
</template>

<style scoped>
.stat { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.lbl { font-size: 11.5px; color: var(--muted); }
.fld { font-size: 14px; font-weight: 700; padding: 2px 6px; background: var(--line-2); color: var(--text); border: 2px solid; border-color: var(--line) var(--line-2) var(--line-2) var(--line); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.fld.ok { color: var(--ok); } .fld.warn { color: var(--warn); } .fld.bad { color: var(--bad); }
</style>
