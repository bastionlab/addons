<script setup lang="ts">
/** "🔥 12": scheduled days done in a row (bumps when it grows) */
const props = defineProps<{ n: number, best?: number, weekly?: boolean }>()
const { t } = useI18n()
const el = ref<HTMLElement>()
watch(() => props.n, (n, o) => {
  if (n > o && !matchMedia('(prefers-reduced-motion: reduce)').matches)
    el.value?.animate([{ transform: 'scale(1)' }, { transform: 'scale(1.45) rotate(-8deg)' }, { transform: 'scale(1)' }], { duration: 520, easing: 'cubic-bezier(.3, 1.4, .5, 1)' })
})
</script>

<template>
  <span v-if="n" ref="el" class="hchip" :title="t(weekly ? 'habits.inARowWeeks' : 'habits.inARow', { n, best: best ?? n })"><HabitsFlame />{{ n }}</span>
</template>

<style scoped>
.hchip { flex: none; display: inline-flex; align-items: center; gap: 3px; padding: 3px 9px; border-radius: 999px; background: var(--warn-soft); color: var(--warn); font-size: 12px; font-weight: 650; font-variant-numeric: tabular-nums; }
.hchip svg { animation: flicker 2.4s ease-in-out infinite; transform-origin: 50% 90%; }
@keyframes flicker { 0%, 100% { transform: scale(1) rotate(0) } 25% { transform: scale(1.08, .94) rotate(-4deg) } 50% { transform: scale(.95, 1.07) rotate(3deg) } 75% { transform: scale(1.05) rotate(-2deg) } }
@media (prefers-reduced-motion: reduce) { .hchip svg { animation: none; } }
</style>
