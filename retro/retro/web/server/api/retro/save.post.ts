/** a save from the player (raw body): srm = the game's own save, state = a save state */
export default defineEventHandler(async (event) => {
  const q = getQuery(event)
  const data = await readRawBody(event, false)
  if (!data?.length) throw createError({ statusCode: 400, statusMessage: 'empty save' })
  return agent(event, '/retro/save', { method: 'POST', body: { sys: String(q.sys ?? ''), name: String(q.name ?? ''), kind: String(q.kind ?? ''), data: data.toString('base64') } })
})
