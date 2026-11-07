<script setup lang="ts">
import type { CalEvent } from '../utils/calendar'
/** one event as a list row: time, colour bar, title and a muted line (Agenda, and the selected day under the phone month grid) */
defineProps<{ e: CalEvent }>()
const cal = useCal()
const { t } = useI18n()
</script>

<template>
  <button type="button" class="r" :style="{ '--c': e.color || 'var(--accent)' }" @click="cal.editor.openEdit(e)">
    <i class="bar" />
    <span class="tm">
      <template v-if="calIsAllDay(e)"><b>{{ t('calendar.allDay') }}</b></template>
      <template v-else><b>{{ calTime(calStart(e)) }}</b><span>{{ calTime(calEnd(e)) }}</span></template>
    </span>
    <span class="main">
      <b class="ti">{{ cal.name(e) }}</b>
      <span v-if="e.location" class="loc">{{ e.location }}</span>
    </span>
    <span class="cn">{{ e.calendarName }}</span>
  </button>
</template>

<style scoped>
.r { display: grid; grid-template-columns: 4px 84px minmax(0, 1fr) minmax(0, 180px); align-items: center; gap: 14px; width: 100%; min-height: 52px; padding: 8px 18px; border: 0; border-bottom: 1px solid var(--line); background: none; color: var(--text); font: inherit; text-align: left; cursor: pointer; }
.r:hover { background: var(--panel-2); }
.bar { align-self: stretch; border-radius: 2px; background: var(--c); }
.tm { display: flex; flex-direction: column; font-size: 12px; line-height: 1.3; color: var(--muted); }
.tm b { color: var(--text); font-weight: 600; font-size: 13px; }
.main { display: flex; flex-direction: column; min-width: 0; }
.ti { font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.loc, .cn { font-size: 12px; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
@media (max-width: 640px) {
  /* time first, then the colour bar, then the title with one muted line under it */
  .r { grid-template-columns: 52px 4px minmax(0, 1fr); gap: 12px; padding: 8px 14px; min-height: 56px; }
  .tm { order: 1; }
  .bar { order: 2; }
  .main { order: 3; }
  .cn { display: none; }
}
</style>
