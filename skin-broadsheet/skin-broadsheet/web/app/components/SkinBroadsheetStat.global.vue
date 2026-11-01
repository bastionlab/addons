<script setup lang="ts">
/** Stat as a market-report figure: small-caps label, the value in heavy display serif; warn/bad are inked in colour with a ▲/▼ */
defineProps<{ label?: string, value?: string | number, tone?: string }>()
</script>

<template>
  <div class="bstat">
    <span class="k">{{ label }}</span>
    <b :class="tone"><span v-if="tone === 'bad'" class="ar">{{ '▼' }}</span><span v-else-if="tone === 'warn'" class="ar">{{ '▲' }}</span>{{ value }}</b>
  </div>
</template>

<style scoped>
.bstat { display: flex; flex-direction: column; gap: 0; min-width: 0; font-family: var(--bs-serif); }
.k { font-size: 12px; font-variant: small-caps; text-transform: lowercase; letter-spacing: .08em; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
b { font-family: var(--bs-disp); font-size: 22px; font-weight: 800; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-variant-numeric: oldstyle-nums; }
b.ok { color: var(--ok); }
b.warn { color: var(--warn); font-style: italic; }
b.bad { color: var(--bad); }
.ar { font-size: .55em; vertical-align: .25em; margin-right: 3px; }
@media (max-width: 640px) { b { font-size: 20px; } }
</style>
