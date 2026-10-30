export default defineEventHandler((event) => {
  const q = getQuery(event)
  return agent(event, '/mail/message', { query: { account: String(q.account ?? '').slice(0, 24), uid: String(Math.round(Number(q.uid)) || 0) } })
})
