<script setup lang="ts">
import type { CalForm } from '../composables/useCalEditor'
/** create / edit / delete one event: a centred sheet on desktop, a bottom sheet on a phone */
const cal = useCal()
const ed = cal.editor
const { t } = useI18n()
// keep the last form on screen while the sheet slides out
const last = shallowRef<CalForm | null>(null)
watch(() => ed.form, (f) => { if (f) last.value = f }, { immediate: true })
const f = computed(() => ed.form ?? last.value)

const fine = import.meta.client ? matchMedia('(pointer: fine)').matches : true
const autofocus = computed(() => (!f.value?.id || fine ? '' : undefined))
const ro = computed(() => !!f.value && !f.value.writable)
const days = computed(() => cal.weekdays.map(d => ({ k: CAL_DOW[d.getDay()] as string, label: fmtDate(d, { weekday: 'short' }) })))
const calendar = computed(() => cal.cals.find(c => f.value && c.accountEmail + '|' + c.id === f.value.calKey))
const calColor = computed(() => calendar.value?.backgroundColor || 'var(--accent)')
const choices = computed(() => {
  const list = ed.writableCals
  // an event on a read-only calendar still names its calendar
  return f.value && calendar.value && !list.includes(calendar.value) ? [calendar.value, ...list] : list
})
function toggleDay(k: string) {
  if (!f.value) return
  f.value.days = f.value.days.includes(k) ? f.value.days.filter(x => x !== k) : [...f.value.days, k]
}
</script>

<template>
  <CalSheet :open="!!ed.form" full :label="f?.id ? t('calendar.edit') : t('calendar.new')" @esc="ed.requestClose()" @backdrop="ed.backdrop()">
    <template #header>
      <button type="button" class="btn ghost hb" :disabled="!!ed.busy" @click="ed.requestClose()">{{ ro ? t('calendar.close') : t('calendar.cancel') }}</button>
      <h2 class="ht">{{ f?.id ? t('calendar.edit') : t('calendar.new') }}</h2>
      <button v-if="f?.writable" type="submit" form="cal-ed" class="btn primary hb" :disabled="!!ed.busy">{{ ed.busy === 'save' ? t('calendar.saving') : t('calendar.save') }}</button>
      <span v-else />
    </template>
    <form v-if="f" id="cal-ed" class="ed" @submit.prevent="ed.save()">
      <fieldset :disabled="ro || !!ed.busy" class="fs">
        <input v-model="f.summary" class="ttl" type="text" :placeholder="t('calendar.f.title')" :data-autofocus="autofocus" autocomplete="off" :aria-label="t('calendar.f.title')">

        <div class="line">
          <Icon name="clock" :size="18" class="ic" />
          <div class="col">
            <div class="when">
              <span class="lbl">{{ t('calendar.f.start') }}</span>
              <div class="dt">
                <input v-model="f.sd" type="date" :aria-label="t('calendar.f.startDate')">
                <input v-if="!f.allDay" v-model="f.st" type="time" :aria-label="t('calendar.f.startTime')">
              </div>
              <span class="lbl">{{ t('calendar.f.end') }}</span>
              <div class="dt end">
                <input v-model="f.ed" type="date" :aria-label="t('calendar.f.endDate')">
                <input v-if="!f.allDay" v-model="f.et" type="time" :aria-label="t('calendar.f.endTime')">
              </div>
            </div>
            <div class="sub">
              <label class="chk"><input v-model="f.allDay" type="checkbox"> {{ t('calendar.f.allDay') }}</label>
              <span v-if="!f.allDay" class="faint small">{{ ed.tz }}</span>
            </div>
          </div>
        </div>

        <div class="line">
          <Icon name="calendar" :size="18" class="ic" />
          <div class="col">
            <div class="selwrap">
              <span class="dot sq" :style="{ background: calColor }" />
              <select v-model="f.calKey" :disabled="!!f.id || ro" :aria-label="t('calendar.f.calendar')">
                <option v-for="c in choices" :key="c.accountEmail + c.id" :value="c.accountEmail + '|' + c.id">{{ c.summary }} ({{ c.accountEmail }})</option>
              </select>
            </div>
            <div class="sw" role="group" :aria-label="t('calendar.f.colour')">
              <button type="button" class="chip cc" :class="{ on: !f.colorId }" :aria-pressed="!f.colorId" @click="f.colorId = ''">
                <span class="dot sq" :style="{ background: calColor }" />{{ t('calendar.f.calColor') }}
              </button>
              <button
                v-for="c in CAL_COLOR_IDS" :key="c" type="button" class="swatch" :class="{ on: f.colorId === c }" :style="{ '--c': cal.colors[c] }"
                :aria-label="t('calendar.f.colourN', { n: c })" :aria-pressed="f.colorId === c" @click="f.colorId = c"
              />
            </div>
          </div>
        </div>

        <div class="line">
          <Icon name="refresh-cw" :size="18" class="ic" />
          <div class="col">
            <select v-model="f.rep" :aria-label="t('calendar.f.repeat')">
              <option value="none">{{ t('calendar.rep.none') }}</option>
              <option value="daily">{{ t('calendar.rep.daily') }}</option>
              <option value="weekly">{{ t('calendar.rep.weekly') }}</option>
              <option value="monthly">{{ t('calendar.rep.monthly') }}</option>
              <option value="yearly">{{ t('calendar.rep.yearly') }}</option>
            </select>
            <p v-if="f.id && ed.repeating && f.rep === 'none'" class="faint small hint">{{ t('calendar.rep.keep') }}</p>
            <template v-if="f.rep !== 'none'">
              <div v-if="f.rep === 'weekly'" class="chips" role="group" :aria-label="t('calendar.f.weekdays')">
                <button v-for="x in days" :key="x.k" type="button" class="chip" :class="{ on: f.days.includes(x.k) }" :aria-pressed="f.days.includes(x.k)" @click="toggleDay(x.k)">{{ x.label }}</button>
              </div>
              <div class="end">
                <select v-model="f.endKind" :aria-label="t('calendar.rep.ends')">
                  <option value="never">{{ t('calendar.rep.never') }}</option>
                  <option value="until">{{ t('calendar.rep.until') }}</option>
                  <option value="count">{{ t('calendar.rep.count') }}</option>
                </select>
                <input v-if="f.endKind === 'until'" v-model="f.until" type="date" :aria-label="t('calendar.rep.until')">
                <input v-if="f.endKind === 'count'" v-model.number="f.count" type="number" min="1" :aria-label="t('calendar.rep.count')">
              </div>
            </template>
          </div>
        </div>

        <div class="line">
          <Icon name="map-pin" :size="18" class="ic" />
          <div class="col"><input v-model="f.location" type="text" :placeholder="t('calendar.f.location')" :aria-label="t('calendar.f.location')"></div>
        </div>
        <div class="line">
          <Icon name="file-text" :size="18" class="ic" />
          <div class="col"><textarea v-model="f.description" rows="3" :placeholder="t('calendar.f.description')" :aria-label="t('calendar.f.description')" /></div>
        </div>
      </fieldset>
      <p v-if="ro" class="muted small ro">{{ t('calendar.readonly') }}</p>
      <div v-if="ed.error" class="errbox" role="alert">{{ ed.error }}</div>
    </form>

    <template v-if="!cal.narrow || ed.ask || (f?.id && f.writable)" #footer>
      <div v-if="ed.ask" class="foot ask">
        <span class="q">{{ t(ed.ask === 'save' ? 'calendar.askSave' : 'calendar.askDelete') }}</span>
        <button type="button" class="btn" :disabled="!!ed.busy" @click="ed.choose('one')">{{ t('calendar.one') }}</button>
        <button type="button" class="btn" :disabled="!!ed.busy" @click="ed.choose('all')">{{ t('calendar.all') }}</button>
        <button type="button" class="btn ghost" :disabled="!!ed.busy" @click="ed.ask = ''">{{ t('calendar.back') }}</button>
      </div>
      <div v-else class="foot">
        <button v-if="f?.id && f.writable" type="button" class="btn danger" :class="{ sure: ed.armed === 'del' }" :disabled="!!ed.busy" @click="ed.remove()">
          {{ ed.busy === 'delete' ? t('calendar.deleting') : ed.armed === 'del' ? t('calendar.sure') : t('calendar.delete') }}
        </button>
        <span class="sp" />
        <button type="button" class="btn dsk" :disabled="!!ed.busy" @click="ed.requestClose()">{{ ro ? t('calendar.close') : t('calendar.cancel') }}</button>
        <button v-if="f?.writable" type="submit" form="cal-ed" class="btn primary dsk" :disabled="!!ed.busy">{{ ed.busy === 'save' ? t('calendar.saving') : t('calendar.save') }}</button>
      </div>
    </template>
  </CalSheet>
</template>

<style scoped>
.fs { border: 0; margin: 0; padding: 0; min-width: 0; display: flex; flex-direction: column; gap: 14px; }
/* every field shares one padding; the title is the same box, a little larger and bolder */
.fs input:not([type='checkbox']), .fs select, .fs textarea { padding: 8px 12px; border-radius: var(--radius-sm); }
.fs .ttl { width: 100%; padding: 9px 12px; font-size: 18px; font-weight: 600; color: var(--text); }
.ttl::placeholder { color: var(--faint); font-weight: 500; }
.line { display: flex; gap: 12px; align-items: flex-start; }
.ic { flex: none; margin-top: 8px; color: var(--muted); }
.col { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 8px; }
.col input:not([type='checkbox']), .col select, .col textarea { width: 100%; font-size: 13.5px; }
.col textarea { resize: vertical; min-height: 64px; }

/* start and end on two rows, each with its date and time; the fields shrink instead of clipping */
.when { display: grid; grid-template-columns: 44px minmax(0, 1fr); gap: 8px; align-items: center; }
.dt { display: flex; gap: 8px; min-width: 0; }
.dt input { min-width: 0; font-size: 13.5px; }
.dt input[type='date'] { flex: 1 1 130px; }
.dt input[type='time'] { flex: 0 1 112px; }
.lbl { font-size: 12px; color: var(--muted); }
.sub { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.chk { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; cursor: pointer; min-height: 28px; }
.chk input { width: 16px; height: 16px; margin: 0; }

.selwrap { position: relative; }
.selwrap select { padding-left: 30px; }
.selwrap .dot { position: absolute; left: 11px; top: 50%; transform: translateY(-50%); pointer-events: none; }
.dot.sq { width: 10px; height: 10px; border-radius: 3px; flex: none; }
.sw { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.cc { gap: 7px; padding: 3px 10px; }
.swatch { width: 22px; height: 22px; padding: 0; border-radius: 50%; border: 2px solid transparent; background: var(--c); cursor: pointer; box-shadow: inset 0 0 0 1px rgb(0 0 0 / .18); transition: transform .12s; }
.swatch:hover { transform: scale(1.12); }
.swatch.on { border-color: var(--panel); box-shadow: 0 0 0 2px var(--text); }

.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chips .chip { padding: 3px 10px; }
.end { display: flex; gap: 8px; }
.end select { flex: 1; }
.end input { flex: 1; min-width: 0; }
.hint { margin: 0; }
.ro { margin: 10px 0 0; }
.errbox { margin-top: 12px; font-size: 13px; }

.foot { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.foot .sp { flex: 1; }
.ask .q { flex: 1 1 100%; font-size: 13px; color: var(--muted); }

/* the sheet header (Cancel / title / Save) is phone-only: the desktop footer keeps those two */
.ht { margin: 0; font-size: 16px; font-weight: 600; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hb { min-height: 40px; }
.hb.ghost { justify-self: start; }
.hb.primary { justify-self: end; }

@media (max-width: 640px) {
  .dsk { display: none; }
  .fs input:not([type='checkbox']), .fs select, .fs textarea { min-height: 44px; }
  .fs .ttl { font-size: 18px; }
  .when { grid-template-columns: 44px minmax(0, 1fr); }
  .chk { min-height: 40px; }
  .line { gap: 10px; }
  .swatch { width: 28px; height: 28px; }
  .foot .btn { min-height: 40px; }
  .ask .btn { flex: 1; }
  .ask .btn.ghost { flex: none; }
}
@media (pointer: coarse) { .chips .chip, .cc { min-height: 34px; } }
</style>
