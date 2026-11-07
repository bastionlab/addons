/** poll a "Describe a widget" job: running / failed / done with a cleaned widget (?job=…&id=<widget id>) */
export default defineEventHandler((event) => {
  requireRole(event, 'owner')
  const q = getQuery(event)
  const id = String(q.id ?? '')
  return widgetAiJob(String(q.job ?? ''), /^[a-z0-9][a-z0-9-]{0,39}$/.test(id) ? id : 'new')
})
