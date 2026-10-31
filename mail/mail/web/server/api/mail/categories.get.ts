export default defineEventHandler((event) => {
  const q = getQuery(event)
  return agent(event, '/mail/categories', { query: { account: String(q.account ?? '').slice(0, 24) } })
})
