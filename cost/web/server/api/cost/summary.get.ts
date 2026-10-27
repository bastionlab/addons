/** usage + electricity numbers from agent/cost.py; days is clamped so a typo can't ask for years */
export default defineEventHandler((event) => {
  const n = Math.round(Number(getQuery(event).days))
  const days = Number.isFinite(n) ? Math.min(Math.max(n, 1), 365) : 30
  return agent(event, `/cost/summary?days=${days}`)
})
