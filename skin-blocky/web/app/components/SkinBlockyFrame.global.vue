<script setup lang="ts">
/**
 * Page chrome: no page title (the page shows its own), and on every page change
 * an "Achievement get! / Opened Metrics" toast sliding in at the top for 3 s, like unlocking an advancement.
 */
const props = withDefaults(defineProps<{ path?: string, title?: string, icon?: string }>(), { path: '/', title: '', icon: '' })
const toast = ref<{ id: number, title: string, icon: string } | null>(null)
let seq = 0
let t: ReturnType<typeof setTimeout> | undefined
watch(() => props.path, () => {
  if (!props.title) return
  toast.value = { id: ++seq, title: props.title, icon: props.icon || 'grid' }
  clearTimeout(t)
  t = setTimeout(() => (toast.value = null), 3000)
})
onUnmounted(() => clearTimeout(t))
</script>

<template>
  <div class="bframe">
    <Transition name="bkach">
      <div v-if="toast" :key="toast.id" class="ach" role="status">
        <span class="aslot"><Icon :name="toast.icon" :size="20" /></span>
        <span class="atx"><b>{{ $t('skinBlocky.achievement') }}</b><span>{{ $t('skinBlocky.opened', { page: toast.title }) }}</span></span>
      </div>
    </Transition>
    <slot />
  </div>
</template>

<style scoped>
.bframe { min-width: 0; }
.ach {
  position: fixed; z-index: 92; top: calc(10px + env(safe-area-inset-top, 0px)); left: 50%; margin-left: -150px; width: 300px; max-width: calc(100vw - 20px);
  display: flex; align-items: center; gap: 10px; padding: 8px 12px; pointer-events: none;
  font-family: "Courier New", Courier, monospace; background: rgba(33, 33, 33, .96); border: 2px solid rgba(0, 0, 0, 1);
  box-shadow: inset 0 0 0 2px rgba(85, 85, 85, 1), 4px 4px 0 rgba(0, 0, 0, .4);
}
.aslot { flex: none; display: grid; place-items: center; width: 36px; height: 36px; color: var(--text); background: rgba(139, 139, 139, 1); box-shadow: inset 2px 2px 0 rgba(55, 55, 55, 1), inset -2px -2px 0 rgba(255, 255, 255, 1); }
.atx { display: flex; flex-direction: column; min-width: 0; font-size: 14px; }
.atx b { color: rgba(255, 255, 85, 1); text-shadow: 2px 2px 0 rgba(63, 63, 21, 1); }
.atx span { color: var(--text); text-shadow: 2px 2px 0 rgba(63, 63, 63, 1); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bkach-enter-active { transition: transform .3s steps(6); }
.bkach-leave-active { transition: transform .3s steps(6); }
.bkach-enter-from, .bkach-leave-to { transform: translateY(-140%); }
@media (max-width: 380px) { .ach { left: 10px; margin-left: 0; } }
@media (prefers-reduced-motion: reduce) {
  .bkach-enter-active, .bkach-leave-active { transition: opacity .15s; }
  .bkach-enter-from, .bkach-leave-to { transform: none; opacity: 0; }
}
</style>

<style>
/* page change: a block dissolve; squares grow in a 32 px grid in steps */
@property --skin-blocky-s { syntax: '<length>'; inherits: false; initial-value: 32px; }
html.skin-blocky .skin-blocky-enter-active {
  -webkit-mask-image: linear-gradient(90deg, rgba(0, 0, 0, 1) var(--skin-blocky-s), rgba(0, 0, 0, 0) 0), linear-gradient(180deg, rgba(0, 0, 0, 1) var(--skin-blocky-s), rgba(0, 0, 0, 0) 0);
  mask-image: linear-gradient(90deg, rgba(0, 0, 0, 1) var(--skin-blocky-s), rgba(0, 0, 0, 0) 0), linear-gradient(180deg, rgba(0, 0, 0, 1) var(--skin-blocky-s), rgba(0, 0, 0, 0) 0);
  -webkit-mask-size: 32px 32px; mask-size: 32px 32px;
  -webkit-mask-composite: source-in; mask-composite: intersect;
  animation: skin-blocky-dissolve .32s steps(5) both;
}
html.skin-blocky .skin-blocky-leave-active { transition: opacity .12s steps(3); }
html.skin-blocky .skin-blocky-leave-to { opacity: 0; }
@keyframes skin-blocky-dissolve { from { --skin-blocky-s: 0px; } to { --skin-blocky-s: 32px; } }
@media (prefers-reduced-motion: reduce) {
  html.skin-blocky .skin-blocky-enter-active { -webkit-mask-image: none; mask-image: none; animation: none; transition: opacity .12s; }
  html.skin-blocky .skin-blocky-enter-from { opacity: 0; }
}
</style>
