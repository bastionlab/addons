<script setup lang="ts">
/**
 * Behind everything: newsprint. A warm paper tone with darker, aged edges, a very faint feTurbulence grain
 * (drawn once, static) and the horizontal fold line of a broadsheet folded in half, with a hint of its shadow.
 */
defineProps<{ path?: string }>()
</script>

<template>
  <div class="bs-bd" aria-hidden="true">
    <svg class="grain" width="100%" height="100%">
      <filter id="bs-noise">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" stitchTiles="stitch" />
        <feColorMatrix type="matrix" values="0 0 0 0 0.11  0 0 0 0 0.09  0 0 0 0 0.07  0 0 0 0.9 0" />
      </filter>
      <rect width="100%" height="100%" filter="url(#bs-noise)" />
    </svg>
    <svg class="fibres" width="100%" height="100%">
      <filter id="bs-fibre">
        <feTurbulence type="fractalNoise" baseFrequency="0.012 0.18" numOctaves="2" seed="7" />
        <feColorMatrix type="matrix" values="0 0 0 0 0.35  0 0 0 0 0.27  0 0 0 0 0.15  0 0 0 0.8 0" />
      </filter>
      <rect width="100%" height="100%" filter="url(#bs-fibre)" />
    </svg>
    <div class="fold" />
    <div class="age" />
  </div>
</template>

<style scoped>
.bs-bd { position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; background: var(--bg); }
.grain { position: absolute; inset: 0; opacity: .1; }
.fibres { position: absolute; inset: 0; opacity: .05; }
.fold {
  position: absolute; left: 0; right: 0; top: 50%; height: 34px; transform: translateY(-50%);
  background: linear-gradient(180deg, transparent, rgba(60, 45, 20, .05) 46%, rgba(255, 255, 255, .35) 50%, rgba(60, 45, 20, .07) 54%, transparent);
}
.age { position: absolute; inset: 0; background: radial-gradient(140% 110% at 50% 40%, transparent 55%, rgba(120, 90, 40, .16) 100%); }
</style>
