<script setup lang="ts">
useHead({ title: 'Gate Test · pve' })
const { data, error } = useFetch<any>('/api/zz-gate-test', { server: false })
</script>

<template>
  <div>
    <h2 class="sec">Gate Test</h2>
    <div v-if="error" class="errbox">{{ error.statusMessage || error.message }}</div>
    <Panel v-else title="Hello">
      <p class="muted small">{{ data?.hello ?? 'Loading…' }}</p>
    </Panel>
  </div>
</template>
<style scoped>.x { color: #ff0000; }</style>
