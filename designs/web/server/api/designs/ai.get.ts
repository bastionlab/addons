/** poll a "Describe a look" job: running / failed / done with a cleaned design */
export default defineEventHandler((event) => {
  requireRole(event, 'owner')
  return designAiJob(String(getQuery(event).job ?? ''))
})
