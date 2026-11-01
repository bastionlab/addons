<script setup lang="ts">
/** Stat: small caps label, big rounded figure, tone as a soft glow */
defineProps<{ label?: string, value?: string | number, tone?: string }>()
</script>

<template>
  <div class="gstat"><span class="lbl">{{ label }}</span><b :class="tone">{{ value }}</b></div>
</template>

<style scoped>
.gstat { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.lbl { font-size: 11px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--faint); }
b { font-size: 22px; font-weight: 700; letter-spacing: -.02em; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
b.ok { color: var(--ok); text-shadow: 0 0 18px color-mix(in srgb, var(--ok) 45%, transparent); }
b.warn { color: var(--warn); text-shadow: 0 0 18px color-mix(in srgb, var(--warn) 45%, transparent); }
b.bad { color: var(--bad); text-shadow: 0 0 18px color-mix(in srgb, var(--bad) 45%, transparent); }
@media (max-width: 640px) { b { font-size: 19px; } }
</style>
