<script setup lang="ts">
import type { CalCal } from '../utils/calendar'
/** every calendar of every connected Google account, grouped by account, with a switch in the calendar's own colour */
defineProps<{ heading?: boolean }>()
const cal = useCal()
const { t } = useI18n()
const groups = computed(() => {
  const m = new Map<string, CalCal[]>()
  for (const c of cal.cals) (m.get(c.accountEmail) ?? m.set(c.accountEmail, []).get(c.accountEmail)!).push(c)
  return [...m].map(([email, list]) => ({ email, list: [...list].sort((a, b) => +b.primary - +a.primary || a.summary.localeCompare(b.summary)) }))
})
</script>

<template>
  <div class="cals">
    <h2 v-if="heading" class="h">{{ t('calendar.calendars') }}</h2>
    <p v-if="!groups.length" class="muted small">{{ t('calendar.noCalendars') }}</p>
    <section v-for="g in groups" :key="g.email" class="grp">
      <div class="acc muted small">{{ g.email }}</div>
      <label v-for="c in g.list" :key="c.id" class="row">
        <input type="checkbox" class="sr" :checked="c.selected" @change="cal.toggleCal(c)">
        <span class="box" :class="{ on: c.selected }" :style="{ '--c': c.backgroundColor }" />
        <span class="nm">{{ c.summary }}</span>
      </label>
    </section>
  </div>
</template>

<style scoped>
.cals { display: flex; flex-direction: column; gap: 14px; }
.h { margin: 0; font-size: 13.5px; font-weight: 600; }
.cals > .h { margin-bottom: -6px; }
.grp { display: flex; flex-direction: column; gap: 1px; }
.acc { padding: 0 4px 3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.row { position: relative; display: flex; align-items: center; gap: 10px; min-height: 32px; padding: 0 4px; border-radius: 6px; cursor: pointer; font-size: 13px; }
.row:hover { background: var(--panel-2); }
.sr { position: absolute; opacity: 0; width: 1px; height: 1px; margin: 0; }
.box { width: 16px; height: 16px; flex: none; border-radius: 4px; border: 2px solid var(--c); background: transparent; position: relative; transition: background .12s; }
.box.on { background: var(--c); }
.box.on::after { content: ''; position: absolute; left: 3.5px; top: 0.5px; width: 4px; height: 8px; border: solid var(--bg); border-width: 0 2px 2px 0; transform: rotate(45deg); }
.sr:focus-visible + .box { outline: 2px solid var(--accent); outline-offset: 2px; }
.nm { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
@media (pointer: coarse) { .row { min-height: 42px; } }
</style>
