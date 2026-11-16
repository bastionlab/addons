/**
 * Calendar helpers: dates, how an event sits on a day, and the side-by-side packing of overlapping events.
 * Pure functions (no state), shared by the Cal* components and useCalendar.
 */
export type CalView = 'month' | 'week' | 'day' | 'agenda'
export interface CalWhen { date?: string, dateTime?: string, timeZone?: string }
export interface CalEvent {
  id: string, calendarId: string, accountEmail: string, summary: string, location: string, description: string
  start: CalWhen, end: CalWhen, colorId?: string | null, color: string, calendarName: string
  recurringEventId?: string | null, writable: boolean, htmlLink?: string
}
export interface CalCal {
  id: string, summary: string, backgroundColor: string, accessRole: string, primary: boolean, accountEmail: string, selected: boolean
}
/** an event placed in a day column: minutes from midnight, and which lane (col of cols) it takes */
export interface CalPlaced { e: CalEvent, sm: number, em: number, top: number, h: number, col: number, span: number, cols: number }

/** pixels per hour in the week / day grid */
export const CAL_HOUR = 56

export const calPad = (n: number) => String(n).padStart(2, '0')
export const calYmd = (d: Date) => `${d.getFullYear()}-${calPad(d.getMonth() + 1)}-${calPad(d.getDate())}`
export const calHm = (d: Date) => `${calPad(d.getHours())}:${calPad(d.getMinutes())}`
export const calAddDays = (d: Date, n: number) => { const x = new Date(d); x.setDate(x.getDate() + n); return x }
export const calSod = (d: Date) => { const x = new Date(d); x.setHours(0, 0, 0, 0); return x }
/** ISO week number (Monday-based, week 1 holds the first Thursday) */
export function calWeekNum(d: Date) {
  const x = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()))
  x.setUTCDate(x.getUTCDate() + 4 - (x.getUTCDay() || 7))
  return Math.ceil(((+x - +new Date(Date.UTC(x.getUTCFullYear(), 0, 1))) / 864e5 + 1) / 7)
}
/** a time of day in the viewer's date/time format */
export const calTime = (d: Date) => d.toLocaleTimeString(localePrefs.date, { hour: '2-digit', minute: '2-digit' })

export const calIsAllDay = (e: CalEvent) => !!e.start?.date
export const calStart = (e: CalEvent) => new Date(e.start.dateTime || e.start.date + 'T00:00:00')
export const calEnd = (e: CalEvent) => (e.end.date ? new Date(e.end.date + 'T00:00:00') : new Date(e.end.dateTime as string))
/** all-day and 24 h+ events are drawn as bars; the rest sit on the time grid / get a dot in the month */
export const calIsBar = (e: CalEvent) => calIsAllDay(e) || +calEnd(e) - +calStart(e) >= 864e5

/** events touching a day, bars first, then by start time */
export function calOnDay(events: CalEvent[], d: Date, kind: 'all' | 'bar' | 'timed' = 'all') {
  const a = calSod(d), b = calAddDays(a, 1)
  return events
    .filter(e => calStart(e) < b && calEnd(e) > a && (kind === 'all' || calIsBar(e) === (kind === 'bar')))
    .sort((x, y) => +calIsBar(y) - +calIsBar(x) || +calStart(x) - +calStart(y) || +calEnd(y) - +calEnd(x))
}

/**
 * Lay out one day's timed events: greedy column packing per cluster of overlapping events (like Google), then each
 * event widens over the lanes to its right that nothing in its cluster uses.
 */
export function calPack(events: CalEvent[], d: Date): CalPlaced[] {
  const a = calSod(d), b = calAddDays(a, 1)
  const items = calOnDay(events, d, 'timed').map((e) => {
    const s = calStart(e), en = calEnd(e)
    // wall-clock minutes, so a day with a clock change still lines up with the hour labels
    const sm = s <= a ? 0 : s.getHours() * 60 + s.getMinutes()
    const em = en >= b ? 1440 : en.getHours() * 60 + en.getMinutes()
    return { e, sm: Math.min(sm, 1420), em: Math.max(em, sm + 1), vis: Math.min(1440, Math.max(em, sm + 20)), col: 0, span: 1, cols: 1 }
  }).sort((x, y) => x.sm - y.sm || y.vis - x.vis)

  const out: CalPlaced[] = []
  let cluster: typeof items = []
  let laneEnds: number[] = []
  let clusterEnd = -1
  const flush = () => {
    for (const it of cluster) {
      const others = cluster.filter(o => o !== it && o.sm < it.vis && o.vis > it.sm)
      let span = 1
      while (it.col + span < laneEnds.length && !others.some(o => o.col === it.col + span)) span++
      out.push({ e: it.e, sm: it.sm, em: it.em, top: it.sm / 60 * CAL_HOUR, h: (it.vis - it.sm) / 60 * CAL_HOUR, col: it.col, span, cols: laneEnds.length })
    }
    cluster = []; laneEnds = []; clusterEnd = -1
  }
  for (const it of items) {
    if (cluster.length && it.sm >= clusterEnd) flush()
    let c = laneEnds.findIndex(end => end <= it.sm)
    if (c < 0) { c = laneEnds.length; laneEnds.push(0) }
    laneEnds[c] = it.vis
    it.col = c
    cluster.push(it)
    clusterEnd = Math.max(clusterEnd, it.vis)
  }
  flush()
  return out
}

/** POST with ONE retry after ~1.2 s when the Nuxt-to-agent hop fails (502/503/504 or a network error, e.g. while the agent restarts). Throws the last error.
 *  Not for creating an event (/api/gcal/event): the first request may have reached Google, a retry would duplicate it. */
export async function calPost<T = any>(url: string, body: any): Promise<T> {
  const down = (e: any) => { const c = Number(e?.statusCode ?? e?.status ?? e?.response?.status); return [502, 503, 504].includes(c) || (!c && !e?.data) }
  try { return await $fetch<T>(url, { method: 'POST', body }) } catch (e: any) {
    if (!down(e) || url === '/api/gcal/event') throw e
    await new Promise(r => setTimeout(r, 1200))
    return await $fetch<T>(url, { method: 'POST', body })
  }
}
/** readable text for a failed calPost: the server's own message, or a plain one when the agent could not be reached */
export function calPostError(e: any, unreachable: string): string {
  const c = Number(e?.statusCode ?? e?.status ?? e?.response?.status)
  if ([502, 503, 504].includes(c) || (!c && !e?.data)) return unreachable
  return e?.data?.statusMessage || e?.message || 'failed'
}
