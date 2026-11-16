/** fuzzy name search below a folder: q (words, all must match), root, p */
export default defineEventHandler((event) => {
  const q = getQuery(event)
  return agent(event, '/files/search', { query: { root: String(q.root ?? 'files'), p: String(q.p ?? ''), q: String(q.q ?? '') }, timeout: 45_000 })
})
