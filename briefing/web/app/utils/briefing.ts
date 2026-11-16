/** Daily briefing: turns a stored day's facts into the rows Home's card and /briefing show. Display only; the facts and
 *  what matters were decided on the server (server/utils/briefingCore.ts). */
export interface BriefingSection { id: string, icon: string, title: string, lines: string[], matters: boolean, tone?: 'warn' | 'bad', short: string }
type T = (key: string, params?: Record<string, any>, plural?: number) => string

const ICON: Record<string, string> = { calendar: 'calendar', mail: 'mail-open', deals: 'tag', flats: 'house', jobs: 'briefcase', habits: 'check', system: 'shield', weather: 'map-pin' }
const ORDER = ['calendar', 'mail', 'deals', 'flats', 'jobs', 'habits', 'system', 'weather']

export function briefingSections(facts: any, matters: string[], t: T): BriefingSection[] {
  const out: BriefingSection[] = []
  const add = (id: string, lines: string[], short: string, tone?: 'warn' | 'bad') =>
    out.push({ id, icon: ICON[id]!, title: t(`briefing.sections.${id}`), lines, matters: matters.includes(id), tone, short })
  for (const id of ORDER) {
    const s = facts?.[id]
    if (!s) continue
    if (id === 'calendar') {
      const ev: any[] = s.events ?? []
      add(id, ev.length ? ev.map(e => (e.allDay ? t('briefing.allDay') : e.time) + '  ' + e.title) : [t('briefing.noEvents')], t('briefing.n.events', { n: ev.length }, ev.length))
    } else if (id === 'mail') {
      add(id, [t('briefing.mailLine', { n: s.important, unread: s.unread })], t('briefing.n.mail', { n: s.important }, s.important))
    } else if (id === 'deals' || id === 'flats' || id === 'jobs') {
      const n = `${s.new}${s.capped ? '+' : ''}`
      const pc = s.capped ? 2 : s.new // "7+" is always plural
      const top = (s.top ?? []).map((x: any) => x.title + (x.price != null ? `  ${x.price} EUR` : ''))
      add(id, s.new ? [t(`briefing.huntLine.${id}`, { n }, pc), ...top] : [t('briefing.noNew')], t(`briefing.n.${id}`, { n }, pc))
    } else if (id === 'habits') {
      const due = (s.due ?? []).map((x: any) => `${x.title}${x.streak ? `  (${x.streak})` : ''}`)
      add(id, [t('briefing.habitsLine', { done: s.doneToday, total: s.total, best: s.bestStreak }), ...due], t('briefing.habitsShort', { done: s.doneToday, total: s.total }, s.total))
    } else if (id === 'system') {
      const info: string[] = []
      if (s.backupAgeH != null) info.push(t('briefing.backupAge', { h: s.backupAgeH }))
      if (s.fullestPool) info.push(t('briefing.pool', { name: s.fullestPool.name, pct: s.fullestPool.pct }))
      add(id, s.alerts?.length ? [...s.alerts, ...info] : [t('briefing.noAlerts'), ...info], s.alerts?.length ? t('briefing.n.alerts', { n: s.alerts.length }, s.alerts.length) : t('briefing.noAlerts'), s.alerts?.length ? 'warn' : undefined)
    } else if (id === 'weather') {
      add(id, [t('briefing.weatherLine', { place: s.place, label: s.label, min: s.min, max: s.max }), t('briefing.weatherMore', { rain: s.rainPct, wind: s.windKmh })], `${s.min} / ${s.max} C`)
    }
  }
  return out
}

/** sections that were switched on but could not be read, as one readable line */
export const briefingUnreadable = (facts: any, t: T) =>
  facts?.unavailable?.length ? t('briefing.unreadable', { x: facts.unavailable.map((id: string) => t(`briefing.sections.${id}`)).join(', ') }) : ''
