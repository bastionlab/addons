/** suggestions; depth > 1 = "Load more" (deeper TMDB pages) */
export default defineEventHandler((event) => {
  const { depth } = getQuery(event)
  return agent(event, '/media/discover', { query: { depth: String(depth ?? '1') } })
})
