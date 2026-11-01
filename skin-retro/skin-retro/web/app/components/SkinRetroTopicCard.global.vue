<script setup lang="ts">
/** a Home tile as a small window: title bar with the icon, then the first line, chips and detail rows */
withDefaults(defineProps<{
  to?: string, icon?: string, name?: string, sub?: string, chips?: { text: string, tone?: string }[]
  more?: { text: string, sub?: string, tone?: string }[]
}>(), { to: '/', icon: 'grid', name: '' })
</script>

<template>
  <NuxtLink :to="to" class="topic tile">
    <span class="bar"><Icon :name="icon" :size="15" /><span class="name">{{ name }}</span></span>
    <span class="body">
      <span class="line" :class="chips?.[0]?.tone">{{ chips?.[0]?.text ?? sub }}</span>
      <span v-if="chips && chips.length > 1" class="chips">
        <span v-for="c in chips.slice(1)" :key="c.text" class="pill" :class="c.tone">{{ c.text }}</span>
      </span>
      <span v-for="(m, i) in more ?? []" :key="i" class="row" :class="m.tone">{{ m.text }}<span v-if="m.sub" class="faint"> · {{ m.sub }}</span></span>
    </span>
  </NuxtLink>
</template>

<style scoped>
.tile { display: flex; flex-direction: column; height: 100%; min-width: 0; overflow: hidden; color: var(--text); text-decoration: none; background: var(--panel); border: 2px solid; border-color: var(--line-2) var(--text) var(--text) var(--line-2); padding: 2px; }
.tile:hover { text-decoration: none; }
.bar { display: flex; align-items: center; gap: 6px; padding: 3px 6px; background: var(--accent); color: var(--line-2); font-weight: 700; font-size: 12.5px; }
.name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.body { display: flex; flex-direction: column; gap: 4px; padding: 6px 6px 4px; min-height: 0; overflow: hidden; font-size: 12.5px; }
.line { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.line.ok { color: var(--ok); } .line.warn { color: var(--warn); } .line.bad { color: var(--bad); }
.chips { display: flex; gap: 4px; flex-wrap: wrap; }
.row { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 12px; }
</style>
