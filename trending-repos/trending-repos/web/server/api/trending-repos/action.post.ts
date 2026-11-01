/** Every write to Trending; the action is allowlisted and each argument rebuilt. */
const ACTIONS = ['refresh', 'save', 'dismiss', 'restore', 'star', 'unstar', 'note', 'ask', 'interests']
const REPO = /^[\w.-]{1,100}\/[\w.-]{1,100}$/

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const action = String(body?.action ?? '')
  if (!ACTIONS.includes(action)) throw createError({ statusCode: 400, statusMessage: `unknown action: ${action}` })
  if (action === 'refresh') {
    if (!refreshing()) refresh()
    return { ok: true }
  }
  if (action === 'interests') {
    setInterests(String(body.text ?? ''))
    return { ok: true, interests: getInterests() }
  }
  const repo = String(body.repo ?? '')
  if (!REPO.test(repo) || !getRepo(repo)) throw createError({ statusCode: 404, statusMessage: 'no such repo' })
  if (action === 'save') setState(repo, 'saved')
  else if (action === 'dismiss') setState(repo, 'dismissed')
  else if (action === 'restore') setState(repo, 'new')
  else if (action === 'star' || action === 'unstar') {
    await agentPost('/trending-repos/star', { repo, on: action === 'star' })
    setStarred(repo, action === 'star')
  } else if (action === 'note') {
    const r = getRepo(repo)
    addNote(`${repo}\nhttps://github.com/${repo}\n\n${r.summary}\n\nRuns: ${r.runs}`, [], false)
  } else {
    const history = Array.isArray(body.history) ? body.history.filter((m: any) => m && typeof m.content === 'string') : []
    if (!history.length) throw createError({ statusCode: 400, statusMessage: 'ask something' })
    return { answer: await askRepo(repo, history) }
  }
  return { ok: true }
})
