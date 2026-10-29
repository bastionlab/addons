<script setup lang="ts">
useHead({ title: 'Widgets · Bastion' })
// the same builder as Home's edit mode, as a page: My widgets / Library / Create
const api = useWidgets()
</script>

<template>
  <div class="wp">
    <WidgetsBuilder :api="api" :packs="[]" page @close="navigateTo('/')" />
  </div>
</template>

<style scoped>
.wp { max-width: 640px; margin: 0 auto; }
</style>
