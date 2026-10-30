<script setup lang="ts">
/** deep night sky with four big aurora blobs drifting on 40–60 s loops; paused while the tab is hidden */
defineProps<{ path?: string }>()
const hidden = ref(false)
const onVis = () => (hidden.value = document.hidden)
onMounted(() => { onVis(); document.addEventListener('visibilitychange', onVis) })
onUnmounted(() => document.removeEventListener('visibilitychange', onVis))
</script>

<template>
  <div class="glass-bd" :class="{ paused: hidden }" aria-hidden="true">
    <i class="b b1" /><i class="b b2" /><i class="b b3" /><i class="b b4" />
    <i class="sheen" />
  </div>
</template>

<style scoped>
.glass-bd {
  position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden;
  background:
    radial-gradient(120% 80% at 50% 0%, color-mix(in srgb, var(--accent) 10%, transparent), transparent 60%),
    linear-gradient(180deg, color-mix(in srgb, var(--bg) 92%, rgba(40, 30, 90, 1)), var(--bg));
}
.b { position: absolute; border-radius: 50%; will-change: transform; animation: drift 48s ease-in-out infinite alternate; }
.b1 { width: 70vmax; height: 70vmax; left: -20vmax; top: -25vmax; background: radial-gradient(circle at 50% 50%, rgba(92, 120, 255, .55), rgba(92, 120, 255, 0) 65%); animation-duration: 52s; }
.b2 { width: 60vmax; height: 60vmax; right: -22vmax; top: 10vh; background: radial-gradient(circle at 50% 50%, rgba(178, 92, 255, .42), rgba(178, 92, 255, 0) 65%); animation-name: drift2; animation-duration: 44s; }
.b3 { width: 65vmax; height: 65vmax; left: 5vw; bottom: -35vmax; background: radial-gradient(circle at 50% 50%, rgba(36, 214, 196, .32), rgba(36, 214, 196, 0) 65%); animation-name: drift3; animation-duration: 58s; }
.b4 { width: 45vmax; height: 45vmax; right: 0; bottom: -10vmax; background: radial-gradient(circle at 50% 50%, rgba(255, 96, 170, .28), rgba(255, 96, 170, 0) 65%); animation-name: drift4; animation-duration: 40s; }
.sheen { position: absolute; inset: 0; background: radial-gradient(140% 100% at 50% 120%, rgba(0, 0, 0, .55), transparent 55%); }
@keyframes drift { 0% { transform: translate(0, 0) scale(1); } 50% { transform: translate(18vw, 12vh) scale(1.15); } 100% { transform: translate(6vw, 28vh) scale(.95); } }
@keyframes drift2 { 0% { transform: translate(0, 0) scale(1); } 50% { transform: translate(-16vw, 20vh) scale(.9); } 100% { transform: translate(-6vw, -10vh) scale(1.12); } }
@keyframes drift3 { 0% { transform: translate(0, 0) scale(1.05); } 50% { transform: translate(20vw, -14vh) scale(.92); } 100% { transform: translate(-10vw, -24vh) scale(1.1); } }
@keyframes drift4 { 0% { transform: translate(0, 0) scale(.9); } 50% { transform: translate(-24vw, -18vh) scale(1.2); } 100% { transform: translate(-30vw, 6vh) scale(1); } }
.paused .b { animation-play-state: paused; }
@media (prefers-reduced-motion: reduce) { .b { animation: none; } }
</style>
