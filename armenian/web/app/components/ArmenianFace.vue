<script setup lang="ts">
/** the back of a card: sound, meaning, example (shared by the study screen and the info sheet) */
import type { ArmCard } from '../utils/armenian'
defineProps<{ c: ArmCard }>()
</script>

<template>
  <div class="face">
    <div class="mean">{{ c.en.join(', ') }}</div>
    <div class="sound">
      <span class="tr">{{ c.tr }}</span>
    </div>
    <div v-if="c.cat" class="cat"><span class="pill">{{ c.cat }}</span></div>
    <div v-if="c.ex" class="ex">
      <span class="exw"><span lang="hy" class="hy">{{ c.ex[0] }}</span></span>
      <span class="muted small">{{ c.ex[1] }}</span>
      <span class="small">{{ c.ex[2] }}</span>
    </div>
  </div>
</template>

<style scoped>
.face { display: flex; flex-direction: column; gap: 10px; align-items: center; }
.mean { font-size: 20px; font-weight: 600; text-align: center; }
.sound { display: flex; align-items: center; gap: 6px; font-size: 17px; color: var(--muted); }
.cat { display: flex; justify-content: center; }
.ex { display: flex; flex-direction: column; gap: 2px; align-items: center; text-align: center; border-top: 1px solid var(--line); padding-top: 10px; width: 100%; }
.hy { font-size: 18px; }
.exw { display: inline-flex; align-items: center; gap: 4px; }
</style>
