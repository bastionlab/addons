import type { CalCal, CalEvent, CalView } from '../utils/calendar'

/**
 * Calendar state for the page and its Cal* components: view + cursor, the visible range, calendars and events
 * (Google is the source of truth, /api/gcal/* -> agent gcal.py), navigation, calendar on/off, keyboard shortcuts.
 * The page calls useCalendar() once and provides it; components take it with useCal().
 *
 * Keys (desktop, ignored while typing, with ctrl/meta/alt, or while a dialog is open):
 * M W D A = month / week / day / agenda, T = today, left / right or J / K = previous / next, N = new event.
 */
export function useCalendar() {
  const { t } = useI18n()
  const { optimistic } = useToast()

  const view = ref<CalView>('week')
  const cursor = ref(new Date())
  const cals = ref<CalCal[]>([])
  const colors = ref<Record<string, string>>({})
  const events = ref<CalEvent[]>([])
  const errors = ref<{ account: string, calendar?: string, error: string }[]>([])
  const error = ref('')
  const weekStart = ref(1)
  const ready = ref(false) // first calendars + events are in
  const busy = ref(false)
  const now = ref(new Date())
  const sheet = ref(false) // the Calendars bottom sheet (narrow screens)
  const pick = ref(false) // the "go to date" sheet (narrow screens)

  const mqNarrow = import.meta.client ? matchMedia('(max-width: 640px)') : null
  const mqWide = import.meta.client ? matchMedia('(min-width: 900px)') : null
  const narrow = ref(!!mqNarrow?.matches)
  const wide = ref(!!mqWide?.matches)
  const mqUpdate = () => { narrow.value = !!mqNarrow?.matches; wide.value = !!mqWide?.matches; if (wide.value) { sheet.value = false; pick.value = false } }

  const todayKey = computed(() => calYmd(now.value))

  // ---- range
  /** the visible range for a view around a date (the month grid is always 6 weeks) */
  const rangeOf = (v: CalView, d: Date): [Date, Date] => {
    const c = calSod(d)
    if (v === 'day') return [c, calAddDays(c, 1)]
    if (v === 'agenda') return [c, calAddDays(c, 30)]
    if (v === 'week') { const s = calAddDays(c, -((c.getDay() - weekStart.value + 7) % 7)); return [s, calAddDays(s, 7)] }
    const f = new Date(c.getFullYear(), c.getMonth(), 1)
    const s = calAddDays(f, -((f.getDay() - weekStart.value + 7) % 7))
    return [s, calAddDays(s, 42)]
  }
  /** the date n periods away (a month in month view, a week, a day, 30 days in the agenda) */
  const shift = (d: Date, n: number): Date => {
    const c = new Date(d)
    if (view.value === 'month') {
      const last = new Date(c.getFullYear(), c.getMonth() + n + 1, 0).getDate()
      return new Date(c.getFullYear(), c.getMonth() + n, Math.min(c.getDate(), last))
    }
    return calAddDays(c, n * (view.value === 'week' ? 7 : view.value === 'agenda' ? 30 : 1))
  }
  const range = computed<[Date, Date]>(() => rangeOf(view.value, cursor.value))
  const days = computed(() => { const [s, e] = range.value; const out: Date[] = []; for (let d = s; d < e; d = calAddDays(d, 1)) out.push(d); return out })
  /** weekday names in the viewer's format, first day of the week first */
  const weekdays = computed(() => Array.from({ length: 7 }, (_, i) => calAddDays(new Date(2024, 0, 7), weekStart.value + i)))

  const span = (a: Date, b: Date, o: Intl.DateTimeFormatOptions) => {
    try { return new Intl.DateTimeFormat(localePrefs.date, o).formatRange(a, b) } catch { return `${fmtDate(a, o)} - ${fmtDate(b, o)}` }
  }
  const title = computed(() => {
    const [s] = range.value, c = cursor.value
    if (view.value === 'month') return fmtDate(c, { month: 'long', year: 'numeric' })
    if (view.value === 'day') return fmtDate(c, narrow.value ? { weekday: 'short', day: 'numeric', month: 'long', ...(c.getFullYear() !== now.value.getFullYear() ? { year: 'numeric' } : {}) } : { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
    const e = calAddDays(s, view.value === 'week' ? 6 : 29)
    // a phone drops the year while the range stays inside this one
    const yr = !narrow.value || s.getFullYear() !== now.value.getFullYear() || e.getFullYear() !== now.value.getFullYear()
    return span(s, e, { day: 'numeric', month: 'short', ...(yr ? { year: 'numeric' } : {}) })
  })
  /** the small line under the title on a phone: which view, and the week number where that helps */
  const subtitle = computed(() => {
    const wk = t('calendar.weekN', { n: calWeekNum(view.value === 'week' ? range.value[0] : cursor.value) })
    return view.value === 'agenda' ? t('calendar.view.agenda') : view.value === 'month' ? '' : wk
  })
  /** false when what is on screen does not include today (the phone header then offers a Today pill) */
  const onToday = computed(() => {
    if (view.value === 'day') return calYmd(cursor.value) === todayKey.value
    if (view.value === 'month') return cursor.value.getFullYear() === now.value.getFullYear() && cursor.value.getMonth() === now.value.getMonth()
    const [s, e] = range.value
    return now.value >= s && now.value < e
  })

  // ---- data
  const hiddenKeys = computed(() => new Set(cals.value.filter(c => !c.selected).map(c => c.accountEmail + '|' + c.id)))
  /** events of the calendars that are switched on (a toggle shows at once, before the refetch) */
  const visible = computed(() => events.value.filter(e => !hiddenKeys.value.has(e.accountEmail + '|' + e.calendarId)))
  const noAccount = computed(() => ready.value && !cals.value.length && !errors.value.length && !error.value)
  const name = (e: CalEvent) => e.summary || t('calendar.noTitleShort')

  const failure = (x: any) => ({ ok: false, error: x?.data?.statusMessage || x?.message || 'failed' })
  let calsLoaded = false
  async function loadCals() {
    const r: any = await $fetch('/api/gcal/calendars').catch(failure)
    if (!r.ok) { error.value = r.error; return }
    cals.value = r.calendars; colors.value = r.colors || {}; errors.value = r.errors || []
    weekStart.value = r.week_start === 'sunday' ? 0 : 1
  }

  // Client cache of fetched windows (previous + current + next period in one request), stale-while-revalidate:
  // paging shows what is known at once and refreshes in the background.
  interface Win { start: Date, end: Date, events: CalEvent[], errors: { account: string, calendar?: string, error: string }[], at: number }
  const cache = new Map<string, Win>()
  const STALE = 90_000, MAX_WINS = 12
  const wkey = (s: Date, e: Date) => s.toISOString() + '|' + e.toISOString()
  /** the window around the cursor shifted by n periods: previous start .. next end */
  const windowAt = (n: number): [Date, Date] => {
    const c = shift(cursor.value, n)
    return [rangeOf(view.value, shift(c, -1))[0], rangeOf(view.value, shift(c, 1))[1]]
  }
  const evKey = (ev: { accountEmail: string, calendarId: string, id: string }) => ev.accountEmail + '|' + ev.calendarId + '|' + ev.id
  const inRange = (ev: CalEvent, s: Date, e: Date) => { try { return calStart(ev) < e && calEnd(ev) > s } catch { return false } }

  // Writes applied locally (key -> what, when). For RECENT_MS a fetch result is corrected by them, so Google-side lag
  // or an old cached answer can neither hide a just-saved event nor bring a just-deleted one back.
  interface Recent { kind: 'upsert' | 'delete', at: number, ev: CalEvent, all: boolean }
  const recent = new Map<string, Recent>()
  const RECENT_MS = 5000
  function reconcile(list: CalEvent[], s: Date, e: Date): CalEvent[] {
    const now = Date.now()
    let out = list
    for (const [k, w] of [...recent]) {
      if (now - w.at > RECENT_MS) { recent.delete(k); continue }
      const rid = w.ev.recurringEventId
      const same = (x: CalEvent) => evKey(x) === k || (w.all && !!rid && x.accountEmail === w.ev.accountEmail && x.calendarId === w.ev.calendarId && x.recurringEventId === rid)
      if (w.kind === 'delete') out = out.filter(x => !same(x))
      else {
        out = out.filter(x => evKey(x) !== k)
        if (inRange(w.ev, s, e)) out = [...out, w.ev]
      }
    }
    return out
  }

  /**
   * A write succeeded: change the visible events and every cached window at once (the refetch that follows only reconciles).
   * `ev` is the normalised event for 'upsert', {id, accountEmail, calendarId, recurringEventId} for 'delete'.
   */
  function applyWrite(kind: 'upsert' | 'delete', ev: CalEvent, scope: 'one' | 'all' = 'one') {
    const all = kind === 'delete' && scope === 'all'
    const k = evKey(ev)
    recent.set(k, { kind, at: Date.now(), ev, all })
    const rid = ev.recurringEventId
    const apply = (list: CalEvent[], s: Date, e: Date) => {
      const rest = list.filter(x => evKey(x) !== k && !(all && rid && x.accountEmail === ev.accountEmail && x.calendarId === ev.calendarId && x.recurringEventId === rid))
      return kind === 'upsert' && inRange(ev, s, e) ? [...rest, ev] : rest
    }
    for (const w of cache.values()) w.events = apply(w.events, w.start, w.end)
    const [s, e] = range.value
    events.value = apply(events.value, s, e)
    show()
  }

  let epoch = 0 // bumped by reload / toggle: answers that started before it are stale and not cached
  function put(s: Date, e: Date, r: any) {
    const k = wkey(s, e)
    cache.delete(k)
    cache.set(k, { start: s, end: e, events: reconcile(r.events || [], s, e), errors: r.errors || [], at: Date.now() })
    while (cache.size > MAX_WINS) cache.delete(cache.keys().next().value as string)
  }
  /** the freshest window that covers the range, else the union of every window touching it, else null */
  function known(): { events: CalEvent[], errors: Win['errors'], fresh: boolean } | null {
    const [s, e] = range.value
    let best: Win | null = null
    const touching: Win[] = []
    for (const w of cache.values()) {
      if (w.start < e && w.end > s) touching.push(w)
      if (w.start <= s && w.end >= e && (!best || w.at > best.at)) best = w
    }
    if (best) return { events: best.events, errors: best.errors, fresh: Date.now() - best.at < STALE }
    if (!touching.length) return null
    const seen = new Set<string>(), out: CalEvent[] = []
    for (const w of touching.sort((x, y) => y.at - x.at)) for (const ev of w.events) {
      const k = ev.accountEmail + '|' + ev.calendarId + '|' + ev.id + '|' + JSON.stringify(ev.start)
      if (!seen.has(k)) { seen.add(k); out.push(ev) }
    }
    return { events: out, errors: touching[0]!.errors, fresh: false }
  }
  /** show what is known for the visible range; with nothing cached the old events stay (they are filtered by day) */
  function show(): boolean {
    const k = known()
    if (!k) return false
    events.value = k.events; errors.value = k.errors
    return k.fresh
  }
  const fetchWin = (s: Date, e: Date): Promise<any> =>
    $fetch('/api/gcal/events', { query: { start: s.toISOString(), end: e.toISOString() } }).catch(failure)

  let seq = 0, pre = 0
  async function loadEvents() {
    const my = ++seq, ep = epoch, [s, e] = windowAt(0)
    pre++
    busy.value = true
    const r: any = await fetchWin(s, e)
    if (my !== seq) return // a newer request is on its way
    if (r.ok && ep === epoch) put(s, e, r)
    busy.value = false
    if (!r.ok) { error.value = r.error; ready.value = true; return }
    error.value = ''; show(); ready.value = true
    prefetch()
  }
  /** one period further in each direction, at low priority, errors ignored */
  function prefetch() {
    const mine = ++pre
    const run = async () => {
      for (const n of [2, -2]) {
        if (mine !== pre) return
        const [s, e] = windowAt(n), w = cache.get(wkey(s, e))
        if (w && Date.now() - w.at < STALE) continue
        const ep = epoch
        const r: any = await fetchWin(s, e)
        if (r.ok && ep === epoch) put(s, e, r)
      }
    }
    setTimeout(() => { if (mine === pre) run() }, 600)
  }
  /** after a write or a calendar toggle: forget the cache, refetch, the old events stay on screen meanwhile */
  const reload = () => { epoch++; cache.clear(); return loadEvents() }
  let settleTimer: any
  /** after a write: refetch now and once more shortly after, so a lagging Google read cannot leave stale data */
  const settle = () => { reload(); clearTimeout(settleTimer); settleTimer = setTimeout(reload, 2500) }
  async function tick() { if (calsLoaded) await loadEvents() }
  usePoll(tick, 120_000)
  watch(() => range.value.map(Number).join(), () => {
    if (!calsLoaded) return
    if (show()) { seq++; busy.value = false; prefetch() } else loadEvents() // fresh window known: nothing to fetch
  })

  async function toggleCal(c: CalCal) {
    const want = !c.selected
    epoch++
    await optimistic(
      () => { c.selected = want },
      () => { c.selected = !want },
      async () => {
        let r: any
        try { r = await calPost('/api/gcal/select', { account: c.accountEmail, calendarId: c.id, selected: want }) } catch (x: any) { throw new Error(calPostError(x, t('calendar.err.unreachable'))) }
        if (!r?.ok) throw new Error(r?.error || 'failed')
      },
      t('calendar.what.select'),
    )
    reload()
  }

  // ---- navigation
  function step(n: number) { cursor.value = shift(cursor.value, n) }
  const today = () => { cursor.value = new Date() }
  const setView = (v: CalView) => { view.value = v }
  /** jump to a date, keeping the view */
  const jump = (d: Date) => { cursor.value = new Date(d); sheet.value = false; pick.value = false }
  const goDay = (d: Date) => { cursor.value = new Date(d); view.value = 'day' }

  const editor = reactive(useCalEditor({ cals, cursor, now, loadEvents: settle, applyWrite }))

  // ---- keyboard
  const KEYS: Record<string, () => void> = {
    m: () => setView('month'), w: () => setView('week'), d: () => setView('day'), a: () => setView('agenda'),
    t: today, arrowleft: () => step(-1), j: () => step(-1), arrowright: () => step(1), k: () => step(1), n: () => editor.openNew(),
  }
  function onKey(e: KeyboardEvent) {
    if (e.ctrlKey || e.metaKey || e.altKey || e.defaultPrevented) return
    if (editor.form || sheet.value || pick.value) return
    const el = e.target as HTMLElement | null
    if (el && (el.isContentEditable || el.closest?.('input, textarea, select, [contenteditable]'))) return
    if (document.querySelector('[aria-modal="true"]')) return
    const fn = KEYS[e.key.toLowerCase()]
    if (!fn) return
    e.preventDefault()
    if (e.repeat && e.key.toLowerCase() === 'n') return
    fn()
  }

  let timer: any
  onMounted(async () => {
    if (deviceKind() === 'phone') view.value = 'day'
    mqNarrow?.addEventListener('change', mqUpdate); mqWide?.addEventListener('change', mqUpdate); mqUpdate()
    window.addEventListener('keydown', onKey)
    timer = setInterval(() => { now.value = new Date() }, 60_000)
    await loadCals()
    calsLoaded = true
    await loadEvents()
  })
  onUnmounted(() => {
    mqNarrow?.removeEventListener('change', mqUpdate); mqWide?.removeEventListener('change', mqUpdate)
    window.removeEventListener('keydown', onKey)
    clearInterval(timer); clearTimeout(settleTimer)
  })

  return reactive({
    view, cursor, cals, colors, events, errors, error, weekStart, ready, busy, now, sheet, pick, narrow, wide, todayKey,
    range, days, weekdays, title, subtitle, onToday, visible, noAccount, name, editor,
    loadCals, loadEvents, reload, toggleCal, step, today, setView, jump, goDay,
  })
}

export type Cal = ReturnType<typeof useCalendar>
/** the calendar the page provided */
export const useCal = () => inject<Cal>('cal') as Cal
