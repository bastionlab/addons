export default defineEventHandler((event) => {
  const q = getQuery(event)
  const pick = (k: string, max = 80) => String(q[k] ?? '').slice(0, max)
  return agent(event, '/mail/messages', { query: { account: pick('account', 24), category: pick('category', 24), unread: pick('unread', 1), q: pick('q') } })
})
