<script setup lang="ts">
/** Money's part of /settings: the bank + Trade Republic setup and which money events go to Discord */
const { data: d, refresh } = useFetch<any>('/api/money', { server: false })
</script>

<template>
  <div>
    <Skeleton v-if="!d" kind="rows" :n="3" />
    <template v-else>
      <MoneySetup :d="d" @changed="refresh" />
      <MoneyNotify class="gap" :n="d.setup?.notify" @changed="refresh" />
    </template>
  </div>
</template>

<style scoped>
.gap { margin-top: 14px; }
</style>
