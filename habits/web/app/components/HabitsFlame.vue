<script setup lang="ts">
/** the streak flame (filled, takes the text colour) */
withDefaults(defineProps<{ size?: number }>(), { size: 13 })
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path d="M12 2c1 3.5-1.5 5.5-3 7.5C7.6 11.4 7 13 7 14.5a5 5 0 0 0 10 0c0-2-1-3.6-2-4.8.1 1.6-.6 2.8-1.6 3.3.5-3.5-.3-7.8-1.4-11z" />
  </svg>
</template>
