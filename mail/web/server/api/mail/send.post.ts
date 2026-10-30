// the only route that sends: the page asks twice, and the agent refuses without confirm: true
export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  if (b?.confirm !== true) throw createError({ statusCode: 400, statusMessage: 'sending needs confirmation' })
  const s = (v: any, n: number) => String(v ?? '').slice(0, n)
  return agent(event, '/mail/send', { method: 'POST', body: {
    account: s(b.account, 24), to: s(b.to, 300), subject: s(b.subject, 300), text: s(b.text, 20000),
    in_reply_to: s(b.in_reply_to, 500), references: s(b.references, 2000), confirm: true,
  } })
})
