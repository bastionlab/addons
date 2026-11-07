<script setup lang="ts">
/** month in miniature: click a day to jump there; the period on screen is highlighted, today is the filled circle */
const cal = useCal()
const { t } = useI18n()
const first = (d: Date) => new Date(d.getFullYear(), d.getMonth(), 1)
const shown = ref(first(cal.cursor))
watch(() => +first(cal.cursor), () => { shown.value = first(cal.cursor) })

const cells = computed(() => {
  const f = shown.value
  const s = calAddDays(f, -((f.getDay() - cal.weekStart + 7) % 7))
  return Array.from({ length: 42 }, (_, i) => calAddDays(s, i))
})
const weekView = computed(() => cal.view === 'week')
const inSel = (d: Date) => (weekView.value ? d >= cal.range[0] && d < cal.range[1] : calYmd(d) === calYmd(cal.cursor))
const move = (n: number) => { shown.value = new Date(shown.value.getFullYear(), shown.value.getMonth() + n, 1) }
</script>

<template>
  <div class="mini">
    <div class="mh">
      <strong>{{ fmtDate(shown, { month: 'long', year: 'numeric' }) }}</strong>
      <button type="button" class="btn ghost icon sm" :aria-label="t('calendar.prev')" @click="move(-1)"><Icon name="chevron-left" :size="16" /></button>
      <button type="button" class="btn ghost icon sm" :aria-label="t('calendar.next')" @click="move(1)"><Icon name="chevron-right" :size="16" /></button>
    </div>
    <div class="g">
      <span v-for="d in cal.weekdays" :key="+d" class="wd">{{ fmtDate(d, { weekday: 'narrow' }) }}</span>
      <button
        v-for="(d, i) in cells" :key="+d" type="button" class="c"
        :class="{ out: d.getMonth() !== shown.getMonth(), today: calYmd(d) === cal.todayKey, sel: inSel(d), l: !weekView || i % 7 === 0, r: !weekView || i % 7 === 6 }"
        :aria-label="fmtDate(d, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })" @click="cal.jump(d)"
      ><span class="n">{{ d.getDate() }}</span></button>
    </div>
  </div>
</template>

<style scoped>
.mh { display: flex; align-items: center; gap: 2px; margin-bottom: 6px; }
.mh strong { flex: 1; font-size: 13.5px; font-weight: 600; }
.mh .btn.icon { width: 28px; height: 28px; padding: 0; }
.g { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); row-gap: 1px; }
.wd { text-align: center; font-size: 11px; color: var(--faint); padding-bottom: 4px; }
.c { height: 32px; padding: 0; border: 0; background: none; color: var(--text); font: inherit; font-size: 12.5px; cursor: pointer; display: grid; place-items: center; }
.c.out { color: var(--faint); }
.c.sel { background: var(--accent-soft); color: var(--accent); border-radius: 0; }
.c.sel.l { border-top-left-radius: 8px; border-bottom-left-radius: 8px; }
.c.sel.r { border-top-right-radius: 8px; border-bottom-right-radius: 8px; }
.n { display: grid; place-items: center; width: 26px; height: 26px; border-radius: 50%; transition: background .15s; }
.c:hover:not(.sel) .n { background: var(--panel-2); }
.c.today .n { background: var(--accent); color: var(--bg); font-weight: 700; }
@media (pointer: coarse) { .c { height: 36px; } .mh .btn.icon { width: 34px; height: 34px; } }
</style>
