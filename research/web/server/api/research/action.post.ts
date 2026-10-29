/** Every write to Research; the action is allowlisted and each argument rebuilt. */
const ACTIONS = ['ask', 'cancel', 'delete', 'note']

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const action = String(body?.action ?? '')
  if (!ACTIONS.includes(action)) throw createError({ statusCode: 400, statusMessage: `unknown action: ${action}` })
  if (action === 'ask') {
    const question = String(body.question ?? '').replace(/\s+/g, ' ').trim().slice(0, 500)
    if (!question) throw createError({ statusCode: 400, statusMessage: 'what do you want to know?' })
    const depth = (Object.keys(DEPTHS) as string[]).includes(body.depth) ? body.depth : 'thorough'
    return queueResearch(question, depth as Depth)
  }
  const id = Number(body.id)
  if (!Number.isInteger(id)) throw createError({ statusCode: 400, statusMessage: 'which run?' })
  if (action === 'cancel') cancelResearch(id)
  else if (action === 'delete') deleteResearch(id)
  else {
    const r = getResearch(id)
    if (!r?.report) throw createError({ statusCode: 400, statusMessage: 'no report yet' })
    addNote(`${r.question}\n\n${r.report}`, [], false)
  }
  return { ok: true }
})
