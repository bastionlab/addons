<script setup lang="ts">
/** six rows that share the height; up to 3 events a cell, then "+N more" (Day view); dots only on a phone */
const cal = useCal()
const { t } = useI18n()
const LIMIT = 3
const cells = computed(() => cal.days.map((d) => {
  const all = calOnDay(cal.visible, d)
  return { d, key: calYmd(d), all, shown: all.slice(0, LIMIT), more: all.length - LIMIT, out: d.getMonth() !== cal.cursor.getMonth(), today: calYmd(d) === cal.todayKey }
}))
// a tap on a day: phones have no room to add from the cell, so it opens the day
const cellClick = (d: Date) => (cal.narrow ? cal.goDay(d) : cal.editor.openNewOn(d))
const dayLabel = (d: Date) => (d.getDate() === 1 ? fmtDate(d, { day: 'numeric', month: 'short' }) : String(d.getDate()))
</script>

<template>
  <div class="m">
    <div v-for="d in cal.weekdays" :key="'h' + +d" class="mh">{{ fmtDate(d, { weekday: 'short' }) }}</div>
    <div v-for="c in cells" :key="c.key" class="mc" :class="{ out: c.out, today: c.today }" @click="cellClick(c.d)">
      <button type="button" class="num" :aria-label="fmtDate(c.d, { weekday: 'long', day: 'numeric', month: 'long' })" @click.stop="cal.goDay(c.d)">{{ dayLabel(c.d) }}</button>
      <template v-if="!cal.narrow">
        <template v-for="e in c.shown" :key="e.id + c.key">
          <CalBar v-if="calIsBar(e)" :e="e" :day="c.d" />
          <button v-else type="button" class="mev" :style="{ '--c': e.color || 'var(--accent)' }" @click.stop="cal.editor.openEdit(e)">
            <i class="d" /><span class="t">{{ calTime(calStart(e)) }}</span><span class="n">{{ cal.name(e) }}</span>
          </button>
        </template>
        <button v-if="c.more > 0" type="button" class="lnk more" @click.stop="cal.goDay(c.d)">{{ t('calendar.more', { n: c.more }) }}</button>
      </template>
      <div v-else-if="c.all.length" class="dots">
        <i v-for="e in c.all.slice(0, 4)" :key="e.id + c.key" class="d" :style="{ '--c': e.color || 'var(--accent)' }" />
        <span v-if="c.all.length > 4" class="plus">{{ c.all.length - 4 }}+</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.m {
  flex: 1; min-height: 0; overflow: auto; display: grid; gap: 1px; background: var(--line);
  grid-template-columns: repeat(7, minmax(0, 1fr)); grid-template-rows: auto repeat(6, minmax(96px, 1fr));
}
.mh { background: var(--panel); padding: 8px 8px 6px; font-size: 11px; font-weight: 500; letter-spacing: .04em; text-transform: uppercase; color: var(--muted); }
.mc { background: var(--panel); min-width: 0; padding: 4px 4px 3px; display: flex; flex-direction: column; gap: 2px; overflow: hidden; cursor: default; }
.mc.out { background: color-mix(in srgb, var(--bg) 45%, var(--panel)); }
.mc.out .num { color: var(--faint); }
.num { align-self: flex-start; min-width: 24px; height: 24px; padding: 0 6px; border: 0; border-radius: 12px; background: none; color: var(--text); font: inherit; font-size: 12.5px; cursor: pointer; }
.num:hover { background: var(--panel-2); }
.mc.today .num { background: var(--accent); color: var(--bg); font-weight: 700; }
.mev { display: flex; align-items: center; gap: 5px; width: 100%; min-height: 18px; padding: 0 4px; border: 0; border-radius: 4px; background: none; color: var(--text); font: inherit; font-size: 12px; text-align: left; cursor: pointer; }
.mev:hover { background: var(--panel-2); }
.mev .d, .dots .d { width: 8px; height: 8px; border-radius: 50%; background: var(--c); flex: none; }
.mev .t { color: var(--muted); font-size: 11px; white-space: nowrap; }
.mev .n { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; font-weight: 500; }
.more { text-align: left; font-size: 11.5px; padding: 0 4px; color: var(--muted); }
.more:hover { color: var(--text); }
.dots { display: flex; flex-wrap: wrap; gap: 3px; padding: 2px 3px; align-items: center; }
.plus { font-size: 10px; color: var(--muted); }
@media (max-width: 640px) {
  .m { grid-template-rows: auto repeat(6, minmax(64px, 1fr)); }
  .mh { padding: 7px 2px 5px; text-align: center; font-size: 10.5px; }
  .mc { padding: 2px; align-items: center; cursor: pointer; }
  .num { align-self: center; min-width: 28px; height: 28px; border-radius: 14px; padding: 0 4px; }
}
@media (pointer: coarse) { .mev { min-height: 24px; } .more { min-height: 24px; } }
</style>
