/** "Generate now": regenerate today's briefing (same "new since" cutoff, never pushes) */
export default defineEventHandler(async (event) => {
  requireRole(event, 'owner')
  const row = await runBriefing({ force: true })
  if (!row) throw createError({ statusCode: 409, statusMessage: 'a briefing is being written' })
  return { ok: true, today: row }
})
