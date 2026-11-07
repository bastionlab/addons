export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  return agent(event, '/gcal/event', { method: 'POST', body: b })
})
