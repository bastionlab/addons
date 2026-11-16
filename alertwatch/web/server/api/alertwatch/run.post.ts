/** "Investigate now": look into one open alert, ignoring the cooldown */
export default defineEventHandler(async (event) => {
  requireRole(event, 'owner')
  const { key } = (await readBody(event)) ?? {}
  if (typeof key !== 'string' || !key) throw createError({ statusCode: 400, statusMessage: 'key is required' })
  const { agentUrl, agentToken } = useRuntimeConfig()
  const st = await upstream<{ log?: any[] }>('agent', agentUrl, agentToken, '/alertwatch/state', 30_000)
  const entry = (st.log ?? []).find((e: any) => e.key === key && e.closed == null)
  if (!entry) throw createError({ statusCode: 404, statusMessage: 'that alert is not open' })
  const run = await investigateAlerts([entry], true)
  if (!run) throw createError({ statusCode: 409, statusMessage: 'an investigation is still running' })
  return { ok: true, turn: run.turn }
})
