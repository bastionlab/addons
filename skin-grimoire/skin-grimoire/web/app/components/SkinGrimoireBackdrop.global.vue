<script setup lang="ts">
/** The room behind the book: dark leather with a soft warm light from above and a vignette. Still, no animation. */
withDefaults(defineProps<{ path?: string }>(), { path: '/' })
</script>

<template>
  <div class="gm-bd" aria-hidden="true" />
</template>

<style scoped>
.gm-bd {
  position: fixed; inset: 0; z-index: -1; pointer-events: none;
  background:
    radial-gradient(ellipse 90% 60% at 50% -10%, color-mix(in srgb, var(--warn) 9%, transparent), transparent 70%),
    radial-gradient(ellipse at 50% 50%, transparent 55%, rgba(0, 0, 0, .55)),
    var(--bg);
}
</style>
