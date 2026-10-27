/** every write to the Armenian deck; the action is allowlisted and each argument rebuilt */
const ACTIONS = ['answer', 'undo', 'forget', 'settings'] as const
type Action = typeof ACTIONS[number]

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const action = String(body?.action ?? '').slice(0, 20) as Action
  if (!ACTIONS.includes(action)) throw createError({ statusCode: 400, statusMessage: `unknown action: ${action}` })
  if (action === 'undo') return armUndo()
  if (action === 'settings') {
    return armPutSettings({
      ...(body.newPerDay != null ? { newPerDay: Number(body.newPerDay) || 0 } : {}),
      ...(Array.isArray(body.groups) ? { groups: body.groups.slice(0, 60).map(Number) } : {}),
      ...(body.writing != null ? { writing: body.writing === true } : {}),
    })
  }
  // a recognition card is the deck id, its write card `w:<id>`
  const k = String(body.k ?? '').slice(0, 42)
  if (action === 'forget') return armForget(k)
  const secs = Number(body.secs)
  return armAnswer(k, Math.round(Number(body.rating)), secs > 0 && secs < 3600 ? Math.round(secs * 10) / 10 : null)
})
