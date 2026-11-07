/** { def } for a button widget → runs its allowlisted POST. The UI asks for a confirm first; this route re-checks the allowlist. */
export default defineEventHandler(async (event) => {
  requireRole(event, 'owner')
  const body = await readBody(event)
  const d = parseDef(body?.def)
  await widgetPress(event, d)
  return { ok: true }
})
