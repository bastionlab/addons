export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  return agent(event, '/mail/drafts', { method: 'POST', body: { account: String(b?.account ?? '').slice(0, 24), uid: Math.round(Number(b?.uid)) || 0 }, timeout: 240_000 })
})
