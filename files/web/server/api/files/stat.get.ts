export default defineEventHandler((event) => {
  const q = getQuery(event)
  return agent(event, '/files/stat', { query: { root: String(q.root ?? 'files'), p: String(q.p ?? '') } })
})
