export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  return agent(event, '/gcal/event/delete', { method: 'POST', body: b })
})
