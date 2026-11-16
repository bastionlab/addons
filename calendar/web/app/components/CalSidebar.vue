<script setup lang="ts">
/** mini month + calendar list: the desktop sidebar, and the content of the Calendars sheet on a phone */
</script>

<template>
  <div class="sb">
    <CalMini />
    <CalCalendars heading />
  </div>
</template>

<style scoped>
.sb { display: flex; flex-direction: column; gap: 22px; }
</style>
