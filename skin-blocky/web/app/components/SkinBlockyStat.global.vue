<script setup lang="ts">
/** Stat as an inventory slot: a sunken bevelled slot holding the value, its name underneath like an item tooltip */
defineProps<{ label?: string, value?: string | number, tone?: string }>()
</script>

<template>
  <div class="bstat">
    <span class="sl"><b :class="tone">{{ value }}</b></span>
    <span class="lbl">{{ label }}</span>
  </div>
</template>

<style scoped>
.bstat { display: flex; flex-direction: column; align-items: flex-start; gap: 4px; min-width: 0; }
.sl {
  display: inline-flex; align-items: center; max-width: 100%; min-height: 36px; padding: 4px 10px;
  background: rgba(139, 139, 139, .55); box-shadow: inset 2px 2px 0 rgba(40, 40, 40, 1), inset -2px -2px 0 rgba(230, 230, 230, .85);
}
b { font-family: "Courier New", Courier, monospace; font-size: 19px; font-weight: 900; color: var(--text); text-shadow: 2px 2px 0 rgba(40, 40, 40, 1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
b.ok { color: var(--ok); } b.warn { color: var(--warn); } b.bad { color: var(--bad); }
.lbl { font-size: 11px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); text-shadow: 1px 1px 0 rgba(40, 40, 40, 1); max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
