export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  return agent(event, '/files/mkdir', { method: 'POST', body: { root: String(b?.root ?? ''), p: String(b?.p ?? ''), name: String(b?.name ?? '') } })
})
