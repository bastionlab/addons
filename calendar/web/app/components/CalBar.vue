<script setup lang="ts">
import type { CalEvent } from '../utils/calendar'
/** an all-day / multi-day event as a tinted bar; the ends are squared where it carries on into the next / from the previous day */
const props = defineProps<{ e: CalEvent, day: Date }>()
const cal = useCal()
const a = computed(() => calSod(props.day))
const cl = computed(() => calStart(props.e) < a.value)
const cr = computed(() => calEnd(props.e) > calAddDays(a.value, 1))
</script>

<template>
  <button type="button" class="bar" :class="{ cl, cr }" :style="{ '--c': e.color || 'var(--accent)' }" @click.stop="cal.editor.openEdit(e)">{{ cal.name(e) }}</button>
</template>

<style scoped>
.bar {
  display: block; width: 100%; min-height: 20px; padding: 1px 6px; text-align: left; font: inherit; font-size: 12px; font-weight: 600; line-height: 18px; color: var(--text); cursor: pointer;
  background: color-mix(in srgb, var(--c) 22%, var(--panel)); border: 0; border-left: 3px solid var(--c); border-radius: 5px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; transition: background .15s;
}
.bar:hover { background: color-mix(in srgb, var(--c) 32%, var(--panel)); }
.bar.cl { border-top-left-radius: 0; border-bottom-left-radius: 0; border-left-width: 0; padding-left: 9px; }
.bar.cr { border-top-right-radius: 0; border-bottom-right-radius: 0; }
@media (pointer: coarse) { .bar { min-height: 26px; line-height: 24px; } }
</style>
