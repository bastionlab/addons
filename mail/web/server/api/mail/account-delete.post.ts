export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  if (b?.confirm !== true) throw createError({ statusCode: 400, statusMessage: 'removing an account needs confirmation' })
  return agent(event, '/mail/account/delete', { method: 'POST', body: { id: String(b.id ?? '').slice(0, 24), delete_cache: b.delete_cache !== false } })
})
