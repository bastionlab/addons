<script setup lang="ts">
/** behind everything: a still, dark field with a faint square grid and a vignette. No motion. */
defineProps<{ path?: string }>()
</script>

<template>
  <div class="tac-bg" aria-hidden="true" />
</template>

<style scoped>
.tac-bg {
  position: fixed; inset: 0; z-index: -1; pointer-events: none;
  background:
    radial-gradient(ellipse at 50% 30%, transparent 40%, rgba(0, 0, 0, .55) 100%),
    linear-gradient(color-mix(in srgb, var(--line) 45%, transparent) 1px, transparent 1px) 0 0 / 48px 48px,
    linear-gradient(90deg, color-mix(in srgb, var(--line) 45%, transparent) 1px, transparent 1px) 0 0 / 48px 48px,
    var(--bg);
}
</style>
