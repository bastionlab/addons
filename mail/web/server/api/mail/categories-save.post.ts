// owner-only (the add-on's roles default to owner); the agent refuses without confirm: true
export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  if (b?.confirm !== true) throw createError({ statusCode: 400, statusMessage: 'saving a category needs confirmation' })
  const s = (v: any, n: number) => String(v ?? '').slice(0, n)
  return agent(event, '/mail/categories/save', { method: 'POST', body: { id: s(b.id, 24), name: s(b.name, 60), color: s(b.color, 12), description: s(b.description, 400), pos: b.pos == null ? undefined : Math.round(Number(b.pos)) || 0, enabled: b.enabled == null ? undefined : !!b.enabled, confirm: true } })
})
