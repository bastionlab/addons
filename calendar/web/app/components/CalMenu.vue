<script setup lang="ts">
/** a small dropdown under its trigger (phone header): closes on Escape, on a tap outside and after a choice */
const open = defineModel<boolean>({ default: false })
const root = ref<HTMLElement>()
function away(e: Event) { if (!root.value?.contains(e.target as Node)) open.value = false }
function key(e: KeyboardEvent) { if (e.key === 'Escape') { e.stopPropagation(); open.value = false; root.value?.querySelector<HTMLElement>('[aria-haspopup]')?.focus() } }
watch(open, (o) => {
  if (o) { document.addEventListener('pointerdown', away, true); document.addEventListener('keydown', key, true) }
  else { document.removeEventListener('pointerdown', away, true); document.removeEventListener('keydown', key, true) }
})
onUnmounted(() => { document.removeEventListener('pointerdown', away, true); document.removeEventListener('keydown', key, true) })
</script>

<template>
  <div ref="root" class="pop">
    <slot name="trigger" />
    <Transition name="pm">
      <div v-if="open" class="menu" role="menu" @click="open = false"><slot /></div>
    </Transition>
  </div>
</template>

<style scoped>
.pop { position: relative; flex: none; }
.menu {
  position: absolute; z-index: 30; right: 0; top: calc(100% + 6px); min-width: 190px; padding: 4px; display: flex; flex-direction: column;
  background: var(--panel); border: 1px solid var(--line-2); border-radius: var(--radius); box-shadow: 0 12px 32px rgb(0 0 0 / .4);
}
.menu :deep(button) {
  display: flex; align-items: center; gap: 10px; width: 100%; min-height: 44px; padding: 0 12px; border: 0; border-radius: var(--radius-sm);
  background: none; color: var(--text); font: inherit; font-size: 14px; text-align: left; cursor: pointer;
}
.menu :deep(button:active), .menu :deep(button:hover) { background: var(--panel-2); }
.menu :deep(button.on) { color: var(--accent); }
.menu :deep(button .sp) { flex: 1; }
.pm-enter-active, .pm-leave-active { transition: transform .12s ease, opacity .12s ease; transform-origin: top right; }
.pm-enter-from, .pm-leave-to { opacity: 0; transform: scale(.96); }
@media (prefers-reduced-motion: reduce) { .pm-enter-active, .pm-leave-active { transition: none; } }
</style>
