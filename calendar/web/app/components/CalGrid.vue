<script setup lang="ts">
import type { CalPlaced } from '../utils/calendar'
/**
 * Week and day: sticky header (weekday, big day number, all-day row), hour gutter, 56 px per hour, overlapping events side
 * by side, a "now" line in today's column. Click an empty slot = new event there (30 min snap), click an event = edit.
 */
const cal = useCal()
const { t } = useI18n()
const sc = ref<HTMLElement>()
const HOURS = Array.from({ length: 24 }, (_, i) => i)
const hourLabel = (h: number) => calTime(new Date(2024, 0, 1, h, 0))

const cols = computed(() => cal.days.map(d => ({
  d, key: calYmd(d), today: calYmd(d) === cal.todayKey, we: d.getDay() === 0 || d.getDay() === 6,
  bars: calOnDay(cal.visible, d, 'bar'), placed: calPack(cal.visible, d),
})))
const nowTop = computed(() => (cal.now.getHours() * 60 + cal.now.getMinutes()) / 60 * CAL_HOUR)
const limit = computed(() => (cal.view === 'day' ? 20 : 3))

function scrollToStart() {
  const el = sc.value
  if (!el) return
  const min = cols.value.some(c => c.today) ? Math.max(0, cal.now.getHours() * 60 + cal.now.getMinutes() - 60) : 7 * 60
  el.scrollTop = min / 60 * CAL_HOUR
}
onMounted(() => nextTick(scrollToStart))
watch(() => calYmd(cal.days[0] as Date) + cal.view, () => nextTick(scrollToStart))

function slot(ev: MouseEvent, d: Date) {
  const r = (ev.currentTarget as HTMLElement).getBoundingClientRect()
  const min = Math.min(23 * 60 + 30, Math.max(0, Math.floor((ev.clientY - r.top) / CAL_HOUR * 2) * 30))
  const s = new Date(d.getFullYear(), d.getMonth(), d.getDate(), Math.floor(min / 60), min % 60)
  cal.editor.openNew(s)
}
const lane = (p: CalPlaced) => ({
  top: p.top + 'px', height: Math.max(p.h, 18) - 1 + 'px',
  left: `calc(${p.col / p.cols * 100}% + 2px)`, width: `calc(${p.span / p.cols * 100}% - 4px)`,
  '--c': p.e.color || 'var(--accent)',
})
</script>

<template>
  <div ref="sc" class="gs">
    <div class="gi" :class="{ wide: cols.length > 1 }" :style="{ '--n': cols.length }">
      <div class="gh">
        <div class="corner" />
        <div v-for="c in cols" :key="c.key" class="dh" :class="{ today: c.today, we: c.we }">
          <button type="button" class="dbtn" :disabled="cal.view === 'day'" :aria-label="fmtDate(c.d, { weekday: 'long', day: 'numeric', month: 'long' })" @click="cal.goDay(c.d)">
            <span class="wd">{{ fmtDate(c.d, { weekday: 'short' }) }}</span>
            <span class="dn">{{ c.d.getDate() }}</span>
          </button>
        </div>
        <div class="adl">{{ t('calendar.allDay') }}</div>
        <div v-for="c in cols" :key="'a' + c.key" class="ad" :class="{ today: c.today, we: c.we }">
          <CalBar v-for="e in c.bars.slice(0, limit)" :key="e.id + c.key" :e="e" :day="c.d" />
          <button v-if="c.bars.length > limit" type="button" class="lnk more" @click="cal.goDay(c.d)">{{ t('calendar.more', { n: c.bars.length - limit }) }}</button>
        </div>
      </div>

      <div class="gb">
        <div class="gut">
          <span v-for="h in HOURS.slice(1)" :key="h" class="hl" :style="{ top: h * CAL_HOUR + 'px' }">{{ hourLabel(h) }}</span>
        </div>
        <div v-for="c in cols" :key="c.key" class="col" :class="{ today: c.today, we: c.we }" @click="slot($event, c.d)">
          <button
            v-for="p in c.placed" :key="p.e.id + p.sm" type="button" class="ev" :class="{ one: p.em - p.sm < 30 }" :style="lane(p)"
            @click.stop="cal.editor.openEdit(p.e)"
          >
            <b>{{ cal.name(p.e) }}</b>
            <span class="tm">{{ calTime(calStart(p.e)) }} - {{ calTime(calEnd(p.e)) }}</span>
          </button>
          <div v-if="c.today" class="now" :style="{ top: nowTop + 'px' }"><i /></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.gs { flex: 1; min-height: 0; overflow: auto; overscroll-behavior: contain; }
.gi { --gut: 54px; min-width: 100%; }
.gh, .gb { display: grid; grid-template-columns: var(--gut) repeat(var(--n), minmax(0, 1fr)); }
@media (max-width: 640px) { .gi.wide { min-width: calc(var(--gut) + var(--n) * 78px); } .gi { --gut: 46px; } }

.gh { position: sticky; top: 0; z-index: 5; background: var(--panel); border-bottom: 1px solid var(--line-2); }
.corner, .adl, .gut { position: sticky; left: 0; z-index: 4; background: var(--panel); }
.dh { border-left: 1px solid var(--line); display: grid; place-items: center; padding: 6px 2px 4px; }
.dbtn { display: flex; flex-direction: column; align-items: center; gap: 2px; background: none; border: 0; color: inherit; font: inherit; padding: 2px 8px; border-radius: 8px; cursor: pointer; min-width: 44px; }
.dbtn:disabled { cursor: default; }
.dbtn:not(:disabled):hover .dn { background: var(--panel-2); }
.wd { font-size: 11px; font-weight: 500; letter-spacing: .04em; text-transform: uppercase; color: var(--muted); }
.dn { display: grid; place-items: center; width: 36px; height: 36px; border-radius: 50%; font-size: 20px; font-weight: 500; line-height: 1; transition: background .15s; }
.dh.today .wd { color: var(--accent); }
.dh.today .dn { background: var(--accent); color: var(--bg); font-weight: 700; }
.adl { display: flex; align-items: flex-start; justify-content: flex-end; padding: 8px 8px 0 0; font-size: 10.5px; color: var(--faint); line-height: 1.2; text-align: right; }
.ad { border-left: 1px solid var(--line); min-height: 30px; padding: 3px 3px 5px; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.more { font-size: 11.5px; text-align: left; padding: 0 4px; }
.we { background-color: color-mix(in srgb, var(--text) 2.5%, transparent); }
.today.ad, .today.col { background-color: color-mix(in srgb, var(--accent) 4%, transparent); }

.gb { height: calc(24 * 56px); }
.gut { height: 100%; }
.hl { position: absolute; right: 8px; transform: translateY(-50%); font-size: 11px; color: var(--muted); white-space: nowrap; }
.col {
  position: relative; border-left: 1px solid var(--line); cursor: default;
  background-image:
    linear-gradient(to bottom, var(--line) 1px, transparent 1px),
    linear-gradient(to bottom, color-mix(in srgb, var(--line) 45%, transparent) 1px, transparent 1px);
  background-size: 100% 56px, 100% 28px;
}
.ev {
  position: absolute; z-index: 1; display: flex; flex-direction: column; gap: 1px; padding: 3px 6px; overflow: hidden; text-align: left; font: inherit; font-size: 12px; line-height: 1.25; color: var(--text); cursor: pointer;
  background: color-mix(in srgb, var(--c) 22%, var(--panel)); border: 0; border-left: 3px solid var(--c); border-radius: 6px; box-shadow: 0 0 0 1px var(--panel); transition: background .15s;
}
.ev:hover { background: color-mix(in srgb, var(--c) 32%, var(--panel)); z-index: 2; }
.ev b { font-weight: 600; overflow-wrap: anywhere; }
.ev .tm { color: var(--muted); font-size: 11px; white-space: nowrap; }
.ev.one { flex-direction: row; align-items: center; gap: 6px; padding-top: 0; padding-bottom: 0; }
.ev.one b, .ev.one .tm { white-space: nowrap; }
.ev.one b { overflow: hidden; text-overflow: ellipsis; min-width: 0; }
.now { position: absolute; left: 0; right: 0; z-index: 3; height: 2px; margin-top: -1px; background: var(--accent); pointer-events: none; }
.now i { position: absolute; left: -5px; top: -4px; width: 10px; height: 10px; border-radius: 50%; background: var(--accent); }
</style>
