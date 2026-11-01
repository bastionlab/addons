<script setup lang="ts">
/** Stat as a key/value line from a config dump: `label` over the value; a warn/bad value gets a status tag */
defineProps<{ label?: string, value?: string | number, tone?: string }>()
</script>

<template>
  <div class="tstat">
    <span class="k">{{ label }}<span class="eq">{{ '=' }}</span></span>
    <b :class="tone">{{ value }}<span v-if="tone === 'bad'" class="tg">{{ ' [FAIL]' }}</span><span v-else-if="tone === 'warn'" class="tg">{{ ' [WARN]' }}</span></b>
  </div>
</template>

<style scoped>
.tstat { display: flex; flex-direction: column; gap: 1px; min-width: 0; font-family: var(--tm-mono); }
.k { font-size: 11.5px; color: var(--faint); text-transform: lowercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.eq { color: var(--line-2); margin-left: 2px; }
b { font-size: 20px; font-weight: 700; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
b.ok { color: var(--ok); text-shadow: 0 0 10px color-mix(in srgb, var(--ok) 45%, transparent); }
b.warn { color: var(--warn); text-shadow: 0 0 10px color-mix(in srgb, var(--warn) 45%, transparent); }
b.bad { color: var(--bad); text-shadow: 0 0 10px color-mix(in srgb, var(--bad) 45%, transparent); }
.tg { font-size: 11px; vertical-align: middle; }
@media (max-width: 640px) { b { font-size: 18px; } }
</style>
