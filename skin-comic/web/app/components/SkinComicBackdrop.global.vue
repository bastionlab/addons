<script setup lang="ts">
/** newsprint: paper tone, halftone dots fading in from the corners and slow sunburst rays behind the masthead */
defineProps<{ path?: string }>()
const hidden = ref(false)
const onVis = () => (hidden.value = document.hidden)
onMounted(() => { onVis(); document.addEventListener('visibilitychange', onVis) })
onUnmounted(() => document.removeEventListener('visibilitychange', onVis))
</script>

<template>
  <div class="comic-bd" :class="{ paused: hidden }" aria-hidden="true">
    <i class="rays" />
    <i class="dots dl" />
    <i class="dots dr" />
  </div>
</template>

<style scoped>
.comic-bd { position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; background: var(--bg); }
.rays {
  position: absolute; left: 70%; top: 0; width: 240vmax; height: 240vmax; margin: -120vmax 0 0 -120vmax;
  background: repeating-conic-gradient(from 0deg, rgba(255, 216, 61, .34) 0deg 7deg, rgba(255, 216, 61, 0) 7deg 15deg);
  -webkit-mask-image: radial-gradient(circle, rgba(0, 0, 0, 1) 0%, rgba(0, 0, 0, .5) 25%, rgba(0, 0, 0, 0) 45%);
  mask-image: radial-gradient(circle, rgba(0, 0, 0, 1) 0%, rgba(0, 0, 0, .5) 25%, rgba(0, 0, 0, 0) 45%);
  animation: crays 160s linear infinite; will-change: transform;
}
.dots { position: absolute; width: 70vmax; height: 70vmax; }
.dl {
  left: -10vmax; bottom: -10vmax;
  background: radial-gradient(circle, rgba(227, 38, 47, .32) 2.2px, rgba(227, 38, 47, 0) 2.8px) 0 0 / 11px 11px;
  -webkit-mask-image: radial-gradient(circle at 0% 100%, rgba(0, 0, 0, 1), rgba(0, 0, 0, 0) 65%);
  mask-image: radial-gradient(circle at 0% 100%, rgba(0, 0, 0, 1), rgba(0, 0, 0, 0) 65%);
}
.dr {
  right: -10vmax; top: 30vh;
  background: radial-gradient(circle, rgba(30, 91, 216, .22) 2px, rgba(30, 91, 216, 0) 2.6px) 0 0 / 10px 10px;
  -webkit-mask-image: radial-gradient(circle at 100% 50%, rgba(0, 0, 0, 1), rgba(0, 0, 0, 0) 60%);
  mask-image: radial-gradient(circle at 100% 50%, rgba(0, 0, 0, 1), rgba(0, 0, 0, 0) 60%);
}
@keyframes crays { to { transform: rotate(360deg); } }
.paused .rays { animation-play-state: paused; }
@media (prefers-reduced-motion: reduce) { .rays { animation: none; } }
</style>
