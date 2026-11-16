import type { CalCal, CalEvent } from '../utils/calendar'

/**
 * The event editor's state: open/close, the form, end-follows-start, validation, save / delete (with the
 * "only this event / all events" step for repeating events). Created by useCalendar.
 */
export const CAL_DOW = ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA']
export const CAL_COLOR_IDS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']

export interface CalForm {
  id: string, calKey: string, summary: string, allDay: boolean, sd: string, st: string, ed: string, et: string
  location: string, description: string, colorId: string, rep: string, days: string[], endKind: string, until: string
  count: number, recurringEventId: string, writable: boolean
}

interface Ctx {
  cals: Ref<CalCal[]>
  cursor: Ref<Date>
  now: Ref<Date>
  loadEvents: () => any
  applyWrite: (kind: 'upsert' | 'delete', ev: CalEvent, scope?: 'one' | 'all') => void
}

const tz = typeof Intl !== 'undefined' ? Intl.DateTimeFormat().resolvedOptions().timeZone : ''

export function useCalEditor(ctx: Ctx) {
  const { t } = useI18n()
  const { armed, arm } = useArm()
  const form = ref<CalForm | null>(null)
  const ask = ref<'' | 'save' | 'delete'>('')
  const busy = ref<'' | 'save' | 'delete'>('')
  const error = ref('')
  let snap = ''
  let prevStart = NaN

  const writableCals = computed(() => ctx.cals.value.filter(c => ['owner', 'writer'].includes(c.accessRole)))
  const canCreate = computed(() => writableCals.value.length > 0)
  const repeating = computed(() => !!form.value?.recurringEventId)
  const dirty = computed(() => !!form.value && JSON.stringify(form.value) !== snap)

  const startMs = (f: CalForm) => new Date(f.allDay ? `${f.sd}T12:00:00` : `${f.sd}T${f.st}:00`).getTime()

  function open(f: CalForm) {
    form.value = f
    ask.value = ''; busy.value = ''; error.value = ''
    snap = JSON.stringify(f)
    prevStart = startMs(f)
  }

  function blank(s: Date): CalForm {
    const e = new Date(s); e.setHours(e.getHours() + 1)
    const w = writableCals.value
    const prim = w.find(c => c.primary && c.selected) || w.find(c => c.selected) || w[0]
    return {
      id: '', calKey: prim ? prim.accountEmail + '|' + prim.id : '', summary: '', allDay: false,
      sd: calYmd(s), st: calHm(s), ed: calYmd(e), et: calHm(e), location: '', description: '', colorId: '',
      rep: 'none', days: [CAL_DOW[s.getDay()] as string], endKind: 'never', until: '', count: 10, recurringEventId: '', writable: true,
    }
  }

  /** a new event: at `start` (a clicked slot), else the next full hour today / 09:00 on the day on screen */
  function openNew(start?: Date) {
    if (!canCreate.value) return
    let s = start
    if (!s) {
      s = new Date(ctx.cursor.value)
      if (calYmd(s) === calYmd(ctx.now.value)) s.setHours(ctx.now.value.getHours() + 1, 0, 0, 0)
      else s.setHours(9, 0, 0, 0)
      if (calYmd(s) !== calYmd(ctx.cursor.value)) s = new Date(ctx.cursor.value.getFullYear(), ctx.cursor.value.getMonth(), ctx.cursor.value.getDate(), 23, 0)
    }
    open(blank(s))
  }
  /** a new event on a day (month view): 09:00, or the next full hour if it is today */
  function openNewOn(d: Date) {
    const s = new Date(d)
    if (calYmd(s) === calYmd(ctx.now.value)) s.setHours(Math.min(ctx.now.value.getHours() + 1, 23), 0, 0, 0)
    else s.setHours(9, 0, 0, 0)
    openNew(s)
  }

  function openEdit(e: CalEvent) {
    const s = calStart(e), en = calEnd(e), ad = calIsAllDay(e)
    const last = ad ? calAddDays(en, -1) : en
    open({
      ...blank(s), id: e.id, calKey: e.accountEmail + '|' + e.calendarId, summary: e.summary || '', allDay: ad,
      sd: calYmd(s), st: ad ? '09:00' : calHm(s), ed: calYmd(last), et: ad ? '10:00' : calHm(en),
      location: e.location || '', description: e.description || '', colorId: e.colorId || '', recurringEventId: e.recurringEventId || '', writable: !!e.writable,
    })
  }

  // The end follows the start (keeps the duration). Google answers timeRangeEmpty for end <= start.
  watch(() => (form.value ? `${form.value.sd}T${form.value.st}` : ''), () => {
    const f = form.value
    if (!f) return
    const ns = startMs(f)
    if (isNaN(ns)) return
    if (!isNaN(prevStart) && ns !== prevStart) {
      if (f.allDay) {
        const days = Math.round((ns - prevStart) / 864e5)
        if (f.ed) f.ed = calYmd(calAddDays(new Date(`${f.ed}T12:00:00`), days))
      } else {
        const end = new Date(`${f.ed}T${f.et}:00`)
        if (!isNaN(+end)) { const ne = new Date(+end + (ns - prevStart)); f.ed = calYmd(ne); f.et = calHm(ne) }
      }
    }
    prevStart = ns
  })
  watch(() => form.value?.allDay, () => { if (form.value) prevStart = startMs(form.value) })
  watch(() => form.value && [form.value.sd, form.value.st, form.value.ed, form.value.et, form.value.allDay], () => { error.value = '' })

  /** '' when fine, else the message to show inside the dialog */
  function validate() {
    const f = form.value as CalForm
    if (!f.sd || !f.ed || (!f.allDay && (!f.st || !f.et))) return t('calendar.err.date')
    if (f.allDay) return f.ed < f.sd ? t('calendar.err.endBefore') : ''
    const s = new Date(`${f.sd}T${f.st}:00`), e = new Date(`${f.ed}T${f.et}:00`)
    if (isNaN(+s) || isNaN(+e)) return t('calendar.err.date')
    return e <= s ? t('calendar.err.endBefore') : ''
  }

  function buildBody() {
    const f = form.value as CalForm
    const b: any = { summary: f.summary, location: f.location, description: f.description, colorId: f.colorId || null }
    if (f.allDay) { b.start = { date: f.sd }; b.end = { date: calYmd(calAddDays(new Date(f.ed + 'T00:00:00'), 1)) } }
    else { b.start = { dateTime: `${f.sd}T${f.st}:00`, timeZone: tz }; b.end = { dateTime: `${f.ed}T${f.et}:00`, timeZone: tz } }
    if (f.rep !== 'none') {
      let r = 'RRULE:FREQ=' + f.rep.toUpperCase()
      if (f.rep === 'weekly' && f.days.length) r += ';BYDAY=' + f.days.join(',')
      if (f.endKind === 'until' && f.until) r += ';UNTIL=' + f.until.replace(/-/g, '') + (f.allDay ? '' : 'T235959Z')
      if (f.endKind === 'count') r += ';COUNT=' + Math.max(1, Number(f.count) || 1)
      b.recurrence = [r]
    }
    return b
  }

  const fail = (r: any) => { error.value = String(r?.error || 'failed').slice(0, 280) }
  const post = (url: string, body: any): Promise<any> =>
    calPost(url, body).catch((e: any) => ({ ok: false, error: calPostError(e, t('calendar.err.unreachable')) }))

  function save() {
    const f = form.value
    if (!f || !f.writable || busy.value || ask.value) return
    const msg = validate()
    if (msg) { error.value = msg; return }
    if (repeating.value) { ask.value = 'save'; return }
    doSave('one')
  }
  async function doSave(scope: 'one' | 'all') {
    const f = form.value as CalForm, [account, calendarId] = f.calKey.split('|')
    busy.value = 'save'; error.value = ''
    const r = await post(f.id ? '/api/gcal/event-update' : '/api/gcal/event', { account, calendarId, body: buildBody(), eventId: f.id, scope, recurringEventId: f.recurringEventId })
    busy.value = ''
    if (!r?.ok) { ask.value = ''; fail(r); return }
    // show the change at once (the agent sends the normalised event; a series edit sends refetch), then reconcile
    if (!r.refetch && r.event?.start) ctx.applyWrite('upsert', r.event, scope)
    close(); ctx.loadEvents()
  }

  function remove() {
    const f = form.value
    if (!f || !f.id || !f.writable || busy.value) return
    if (repeating.value) { ask.value = 'delete'; return }
    if (!arm('del')) return
    doDelete('one')
  }
  async function doDelete(scope: 'one' | 'all') {
    const f = form.value as CalForm, [account, calendarId] = f.calKey.split('|')
    busy.value = 'delete'; error.value = ''
    const r = await post('/api/gcal/event-delete', { account, calendarId, eventId: f.id, scope, recurringEventId: f.recurringEventId })
    busy.value = ''
    if (!r?.ok) { ask.value = ''; fail(r); return }
    ctx.applyWrite('delete', { id: String(r.eventId || f.id), accountEmail: account, calendarId, recurringEventId: f.recurringEventId || null } as CalEvent, scope)
    close(); ctx.loadEvents()
  }
  const choose = (scope: 'one' | 'all') => (ask.value === 'save' ? doSave(scope) : doDelete(scope))

  function close() { form.value = null; ask.value = ''; busy.value = ''; error.value = '' }
  /** Cancel / Escape: asks first when there is something to lose */
  function requestClose() {
    if (busy.value) return
    if (dirty.value && !confirm(t('calendar.discard'))) return
    close()
  }
  /** a click outside the dialog only closes it when nothing was typed */
  function backdrop() { if (!dirty.value && !busy.value) close() }

  return { form, ask, busy, error, armed, writableCals, canCreate, repeating, dirty, tz, openNew, openNewOn, openEdit, save, remove, choose, close, requestClose, backdrop }
}
