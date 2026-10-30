// owner-only (the add-on's roles default to owner); the agent refuses without confirm: true
export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  if (b?.confirm !== true) throw createError({ statusCode: 400, statusMessage: 'changing a category needs confirmation' })
  const s = (v: any, n: number) => String(v ?? '').slice(0, n)
  return agent(event, '/mail/message/category', { method: 'POST', body: { account: s(b.account, 24), uid: Math.round(Number(b.uid)) || 0, category: s(b.category, 24), also_rule: b.also_rule ? { kind: s(b.also_rule.kind, 10), value: s(b.also_rule.value, 120) } : undefined, confirm: true } })
})
