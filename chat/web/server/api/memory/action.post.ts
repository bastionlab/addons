/**
 * Every write to the chat memory. Same pattern as notes/action: the action is allowlisted and each argument rebuilt.
 */
const ACTIONS = ['add', 'edit', 'delete', 'pin'] as const
type Action = typeof ACTIONS[number]

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const action = String(body?.action ?? '').slice(0, 20) as Action
  if (!ACTIONS.includes(action)) throw createError({ statusCode: 400, statusMessage: `unknown action: ${action}` })

  if (action === 'add') return addFact(body.text, String(body.src ?? '').replace(/[^\w-]/g, ''))

  const id = Math.round(Number(body?.id))
  if (!id) throw createError({ statusCode: 400, statusMessage: 'missing fact id' })
  if (action === 'edit') return editFact(id, { text: body.text })
  if (action === 'pin') return editFact(id, { pinned: body.pinned !== false })
  return deleteFact(id)
})
