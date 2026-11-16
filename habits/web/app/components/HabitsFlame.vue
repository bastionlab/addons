<script setup lang="ts">
/** the streak flame (filled, takes the text colour) */
withDefaults(defineProps<{ size?: number }>(), { size: 13 })
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path d="M12 2c1 3.5-1.5 5.5-3 7.5C7.6 11.4 7 13 7 14.5a5 5 0 0 0 10 0c0-2-1-3.6-2-4.8.1 1.6-.6 2.8-1.6 3.3.5-3.5-.3-7.8-1.4-11z" />
  </svg>
</template>

<style>
/* the one flicker, shared by the chip, today's streak and the celebration (their rules reference these by name) */
@keyframes flicker { 0%, 100% { transform: scale(1) rotate(0) } 25% { transform: scale(1.08, .94) rotate(-4deg) } 50% { transform: scale(.95, 1.07) rotate(3deg) } 75% { transform: scale(1.05) rotate(-2deg) } }
@keyframes pop-in { from { opacity: 0; transform: scale(.5) } }
@keyframes rise { from { opacity: 0; transform: translateY(10px) } }
</style>
