export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  return agent(event, '/gcal/select', { method: 'POST', body: b })
})
