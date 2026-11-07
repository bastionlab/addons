<script setup lang="ts">
/**
 * Page frame without a title: the owner doesn't want a header that only repeats the tab's name (it used to be an
 * iOS-style large title + a pinned compact header). Full-screen pages (/chat) keep all their height.
 */
defineProps<{ path?: string, title?: string, icon?: string }>()
</script>

<template>
  <div class="gframe">
    <slot />
  </div>
</template>

<style scoped>
.gframe { min-width: 0; padding-top: 4px; }
</style>

<style>
/* page change: fade + a hair of scale */
html.skin-glass .skin-glass-enter-active { transition: opacity .3s ease, transform .34s cubic-bezier(.2, .9, .3, 1.05); }
html.skin-glass .skin-glass-leave-active { transition: opacity .16s ease, transform .16s ease; }
html.skin-glass .skin-glass-enter-from { opacity: 0; transform: scale(.98); }
html.skin-glass .skin-glass-leave-to { opacity: 0; transform: scale(1.01); }
@media (prefers-reduced-motion: reduce) {
  html.skin-glass .skin-glass-enter-active, html.skin-glass .skin-glass-leave-active { transition: opacity .12s; }
  html.skin-glass .skin-glass-enter-from, html.skin-glass .skin-glass-leave-to { transform: none; }
}
</style>
