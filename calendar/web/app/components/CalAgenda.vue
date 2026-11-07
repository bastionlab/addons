<script setup lang="ts">
/** the next 30 days from the cursor: only days that have events, under sticky date headings */
const cal = useCal()
const { t } = useI18n()
const groups = computed(() => cal.days.map((d) => {
  const key = calYmd(d)
  const diff = Math.round((+d - +calSod(cal.now)) / 864e5)
  return {
    d, key, evs: calOnDay(cal.visible, d),
    label: diff === 0 ? t('calendar.today') : diff === 1 ? t('calendar.tomorrow') : fmtDate(d, { weekday: 'long' }),
    date: fmtDate(d, { day: 'numeric', month: 'short', ...(d.getFullYear() !== cal.now.getFullYear() ? { year: 'numeric' } : {}) }),
    today: diff === 0,
  }
}).filter(g => g.evs.length))
</script>

<template>
  <div class="ag">
    <Skeleton v-if="!groups.length && cal.busy" kind="rows" :n="5" />
    <div v-else-if="!groups.length" class="empty-state">{{ t('calendar.empty') }}</div>
    <section v-for="g in groups" :key="g.key" class="day">
      <h2 class="dh" :class="{ today: g.today }"><b>{{ g.label }}</b><span>{{ g.date }}</span></h2>
      <CalRow v-for="e in g.evs" :key="e.id + g.key" :e="e" />
    </section>
  </div>
</template>

<style scoped>
.ag { flex: 1; min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding: 0 0 12px; }
.ag > .empty-state { padding-top: 64px; }
.ag > :deep(.sk) { padding: 12px 16px; }
.dh { position: sticky; top: 0; z-index: 2; margin: 0; padding: 14px 18px 8px; display: flex; align-items: baseline; gap: 10px; background: var(--panel); border-bottom: 1px solid var(--line); font-size: 13px; }
.dh b { font-size: 14px; font-weight: 600; }
.dh span { color: var(--muted); }
.dh.today b { color: var(--accent); }
@media (max-width: 640px) {
  .dh { padding: 12px 14px 7px; }
  .ag { padding-bottom: 84px; } /* clear of the + and the mic */
}
</style>
