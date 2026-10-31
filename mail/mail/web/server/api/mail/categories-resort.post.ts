// owner-only (the add-on's roles default to owner); the agent refuses without confirm: true
export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  if (b?.confirm !== true) throw createError({ statusCode: 400, statusMessage: 're-sorting needs confirmation' })
  const s = (v: any, n: number) => String(v ?? '').slice(0, n)
  return agent(event, '/mail/categories/resort', { method: 'POST', body: { account: s(b.account, 24), only_unsure: !!b.only_unsure, confirm: true } })
})
