// invented facts for the tests (and nothing else): host homelab, people Alex and Sam, example.com
import type { Facts } from '../web/server/utils/briefingCore.ts'

export const quiet = (): Facts => ({
  calendar: { events: [] },
  mail: { unread: 14, important: 0 },
  deals: { new: 0, capped: false, top: [] },
  flats: { new: 0, capped: false, top: [] },
  jobs: { new: 0, capped: false, top: [] },
  habits: { due: [{ title: 'Walk 30 minutes', streak: 4 }], doneToday: 0, total: 1, bestStreak: 4 },
  system: { alerts: [], backupAgeH: 9, fullestPool: { name: 'tank', pct: 61 } },
  weather: { place: 'Berlin', now: 11, min: 8, max: 14, rainPct: 20, windKmh: 15, label: 'cloudy' },
  unavailable: [],
})

export const busy = (): Facts => ({
  calendar: { events: [
    { time: null, title: 'Sam birthday', allDay: true },
    { time: '09:30', title: 'Dentist', allDay: false },
    { time: '14:00', title: 'Call with Alex', allDay: false },
  ] },
  mail: { unread: 31, important: 2 },
  deals: { new: 5, capped: false, top: [{ title: 'RTX 3090 24GB', price: 520 }, { title: 'Mechanical keyboard', price: 35 }] },
  flats: { new: 2, capped: false, top: [{ title: '2 Zimmer, Altbau', price: 980 }] },
  jobs: { new: 7, capped: true, top: [{ title: 'Platform engineer' }] },
  habits: { due: [{ title: 'Walk 30 minutes', streak: 4 }], doneToday: 1, total: 2, bestStreak: 12 },
  system: { alerts: ['Backup of CT 120 failed'], backupAgeH: 31, fullestPool: { name: 'tank', pct: 91 } },
  weather: { place: 'Berlin', now: 9, min: 6, max: 13, rainPct: 80, windKmh: 25, label: 'rain' },
  unavailable: [],
})
