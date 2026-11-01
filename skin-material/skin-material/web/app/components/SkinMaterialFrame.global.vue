<script setup lang="ts">
/**
 * Page frame: no headline. The page's name is already in the nav (and in the top app bar on a phone), and the
 * owner doesn't want a big title repeating it; the frame only keeps Material's page spacing.
 */
defineProps<{ path?: string, title?: string, icon?: string }>()
</script>

<template>
  <div class="m3-frame"><slot /></div>
</template>

<style scoped>
.m3-frame { padding-top: 4px; }
</style>
