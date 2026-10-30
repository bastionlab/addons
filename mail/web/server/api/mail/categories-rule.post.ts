// owner-only (the add-on's roles default to owner); the agent refuses without confirm: true
export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  if (b?.confirm !== true) throw createError({ statusCode: 400, statusMessage: 'adding a rule needs confirmation' })
  const s = (v: any, n: number) => String(v ?? '').slice(0, n)
  return agent(event, '/mail/categories/rule', { method: 'POST', body: { category: s(b.category, 24), kind: s(b.kind, 10), value: s(b.value, 120), apply: !!b.apply, confirm: true } })
})
