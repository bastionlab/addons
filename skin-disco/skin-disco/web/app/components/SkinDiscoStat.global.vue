<script setup lang="ts">
/** Stat: a tiny VU meter, small-caps label and a neon figure */
defineProps<{ label?: string, value?: string | number, tone?: string }>()
</script>

<template>
  <div class="dstat" :class="tone">
    <span class="lbl"><i class="vu" aria-hidden="true"><b /><b /><b /></i>{{ label }}</span>
    <span class="val">{{ value }}</span>
  </div>
</template>

<style scoped>
.dstat { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.lbl { display: inline-flex; align-items: center; gap: 6px; font-size: 10.5px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
.vu { display: inline-flex; align-items: flex-end; gap: 1.5px; height: 10px; }
.vu b { width: 2.5px; height: 100%; background: var(--accent); border-radius: 1px; }
.vu b:nth-child(1) { transform: scaleY(.4); transform-origin: bottom; }
.vu b:nth-child(2) { transform: scaleY(.75); transform-origin: bottom; }
.val { max-width: 100%; font-size: 21px; font-weight: 900; font-style: italic; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-shadow: 0 0 10px rgba(255, 63, 180, .45); }
.ok .val { color: var(--ok); text-shadow: 0 0 10px color-mix(in srgb, var(--ok) 55%, transparent); }
.warn .val { color: var(--warn); text-shadow: 0 0 10px color-mix(in srgb, var(--warn) 55%, transparent); }
.bad .val { color: var(--bad); text-shadow: 0 0 10px color-mix(in srgb, var(--bad) 55%, transparent); }
.ok .vu b { background: var(--ok); } .warn .vu b { background: var(--warn); } .bad .vu b { background: var(--bad); }
</style>
