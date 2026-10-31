// owner-only (the add-on's roles default to owner); the agent refuses without confirm: true
export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  if (b?.confirm !== true) throw createError({ statusCode: 400, statusMessage: 'removing a rule needs confirmation' })
  return agent(event, '/mail/categories/rule-delete', { method: 'POST', body: { id: Math.round(Number(b.id)) || 0, confirm: true } })
})
