/**
 * Habit maths, ported unchanged from the old app (CT 204): local-time days as YYYY-MM-DD, weekday 0 = Monday.
 * Streak = scheduled days done in a row; today only counts once it is done (still open doesn't break it).
 * Perfect day = every habit that existed and was scheduled that day got done.
 */
export type HabitFreq = 'daily' | 'weekly' | 'days'
export interface HabitRow { id: string, title: string, freq: HabitFreq, days: number[], created: number }
export type HabitChecks = Record<string, Set<string>>

export const pad2 = (n: number) => String(n).padStart(2, '0')
export const isoDay = (d: Date = new Date()) => `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
export const parseDay = (s: string) => { const [y, m, d] = s.split('-').map(Number); return new Date(y!, m! - 1, d) }
export const midnight = (d = new Date()) => new Date(d.getFullYear(), d.getMonth(), d.getDate())
export const addDays = (d: Date, n: number) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n)
export const weekdayOf = (d: Date) => (d.getDay() + 6) % 7

export const isScheduled = (h: HabitRow, wd: number) => h.freq === 'daily' || h.days.includes(wd)
export const isDoneOn = (ck: HabitChecks, hid: string, day: string) => !!ck[hid]?.has(day)

export function habitStats(h: HabitRow, ck: HabitChecks, today = midnight()) {
  const done = ck[h.id] ?? new Set<string>()
  let start = midnight(new Date(h.created))
  for (const d of done) { const x = parseDay(d); if (x < start) start = x }
  const from30 = addDays(today, -29)
  let streak = 0, best = 0, due = 0, hit = 0
  for (let d = start; d <= today; d = addDays(d, 1)) {
    if (!isScheduled(h, weekdayOf(d))) continue
    const ok = done.has(isoDay(d)), open = +d === +today && !ok
    if (ok) best = Math.max(best, ++streak)
    else if (!open) streak = 0
    if (d >= from30 && !open) { due++; if (ok) hit++ }
  }
  return { done, start, streak, best, rate: due ? Math.round((hit / due) * 100) : null as number | null, total: done.size }
}

/** true / false / null (nothing due that day) */
export function dayState(hs: HabitRow[], ck: HabitChecks, d: Date): boolean | null {
  const key = isoDay(d)
  const due = hs.filter(h => isScheduled(h, weekdayOf(d)) && midnight(new Date(h.created)) <= d)
  return due.length ? due.every(h => isDoneOn(ck, h.id, key)) : null
}

/** perfect days in a row; days with nothing due are skipped, today still open doesn't break it */
export function perfectStreak(hs: HabitRow[], ck: HabitChecks, t = midnight()) {
  if (!hs.length) return 0
  const first = Math.min(...hs.map(h => +midnight(new Date(h.created))))
  let streak = dayState(hs, ck, t) ? 1 : 0
  for (let d = addDays(t, -1); +d >= first; d = addDays(d, -1)) {
    const s = dayState(hs, ck, d)
    if (s === false) break
    if (s) streak++
  }
  return streak
}

export const MILESTONES = [3, 7, 14, 21, 30, 50, 75, 100, 150, 200, 365, 500, 1000]
