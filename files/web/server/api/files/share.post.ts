/** create (root, p, ttl_hours) or revoke (revoke: token) a public share link */
export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  if (b?.revoke) return agent(event, '/files/share/revoke', { method: 'POST', body: { token: String(b.revoke) } })
  return agent(event, '/files/share', { method: 'POST', body: { root: String(b?.root ?? ''), p: String(b?.p ?? ''), ttl_hours: Number(b?.ttl_hours) || 72 } })
})
