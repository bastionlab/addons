/** the seasons of one series, for the Request picker */
export default defineEventHandler((event) => {
  const { tmdbId } = getQuery(event)
  return agent(event, '/media/discover/seasons', { query: { tmdbId: String(tmdbId ?? '') } })
})
