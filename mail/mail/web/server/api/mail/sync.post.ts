export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  return agent(event, '/mail/sync', { method: 'POST', body: { account: String(b?.account ?? '').slice(0, 24) }, timeout: 300_000 })
})
