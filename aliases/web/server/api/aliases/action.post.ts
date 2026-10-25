/** every write: the action is allowlisted and each argument rebuilt before it goes to the agent */
const ACTIONS = ['login', 'verify', 'logout', 'new', 'import', 'edit', 'active', 'delete', 'refresh'] as const
type Action = typeof ACTIONS[number]
const str = (v: any, n: number) => String(v ?? '').slice(0, n)

export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  const action = str(b?.action, 20) as Action
  if (!ACTIONS.includes(action)) throw createError({ statusCode: 400, statusMessage: `unknown action: ${action}` })
  const body: Record<string, any> = {}
  if (action === 'login') body.user = str(b.user, 80)
  if (action === 'verify') body.otp = str(b.otp, 200)
  if (action === 'new') Object.assign(body, { label: str(b.label, 80), note: str(b.note, 300) })
  if (action === 'import') body.text = str(b.text, 200_000)
  if (['edit', 'active', 'delete'].includes(action)) body.address = str(b.address, 100)
  if (action === 'edit') {
    if (b.label != null) body.label = str(b.label, 80)
    if (b.note != null) body.note = str(b.note, 300)
  }
  if (action === 'active') body.active = !!b.active
  if (action === 'delete') body.deactivate = b.deactivate !== false
  return agent(event, `/aliases/${action}`, { method: 'POST', body, timeout: action === 'refresh' ? 300_000 : 60_000 })
})
