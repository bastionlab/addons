<script setup lang="ts">
/** each page under a thin briefing line: its objective (a themed line per page), nothing for pages without one */
const props = withDefaults(defineProps<{ path?: string, title?: string, icon?: string }>(), { path: '', title: '', icon: '' })
const FULL = ['/chat']
const full = computed(() => FULL.includes(props.path))
const { t, te } = useI18n()
const flavor = computed(() => { const k = `skinTactical.objectives.${props.path.split('/')[1] || 'home'}`; return te(k, 'en') ? t(k) : '' })
</script>

<template>
  <div class="tac-frame">
    <div v-if="!full && flavor" class="brief">{{ $t('skinTactical.objective', { page: flavor }) }}</div>
    <slot />
  </div>
</template>

<style scoped>
.brief {
  margin: 0 0 14px; padding: 2px 0 2px 10px; border-left: 3px solid var(--accent);
  font: 600 12px/1.4 "Bahnschrift", "Arial Narrow", "Roboto Condensed", system-ui, sans-serif;
  text-transform: uppercase; letter-spacing: .12em; color: var(--muted);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
</style>
