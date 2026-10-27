/** "Describe a look": start a Claude job for { ask, base } (the design in the editor); owner only, it uses the Claude plan */
export default defineEventHandler(async (event) => {
  requireRole(event, 'owner')
  const b = await readBody(event)
  const ask = String(b?.ask ?? '').trim()
  if (!ask) throw createError({ statusCode: 400, statusMessage: 'Describe the look first' })
  return designAiStart(ask, b?.base, Array.isArray(b?.images) ? b.images : [])
})
