/** a file's bytes: the agent's answer piped through with Range forwarded (200 / 206 / 416) */
export default defineEventHandler(async (event) => {
  const q = getQuery(event)
  const { agentUrl, agentToken } = useRuntimeConfig(event)
  const qs = new URLSearchParams({ root: String(q.root ?? 'files'), p: String(q.p ?? '') })
  if (q.dl === '1') qs.set('dl', '1')
  const headers: Record<string, string> = { Authorization: `Bearer ${agentToken}` }
  const range = getRequestHeader(event, 'range')
  if (range) headers.Range = range
  const ctl = new AbortController()
  event.node.req.on('close', () => ctl.abort())
  const res = await fetch(`${agentUrl}/files/raw?${qs}`, { headers, signal: ctl.signal }).catch((e: any) => {
    throw createError({ statusCode: 502, statusMessage: `agent: ${e?.message}` })
  })
  if (res.status === 400 || res.status === 404) throw createError({ statusCode: res.status, statusMessage: ((await res.json().catch(() => ({}))) as any).error || 'not found' })
  const out: Record<string, string> = { 'Cross-Origin-Resource-Policy': 'same-origin', 'Cache-Control': 'private, no-cache' }
  for (const h of ['content-type', 'content-length', 'content-range', 'accept-ranges', 'content-disposition', 'content-security-policy', 'x-content-type-options']) {
    const v = res.headers.get(h)
    if (v) out[h] = v
  }
  setResponseStatus(event, res.status)
  setResponseHeaders(event, out)
  if (!res.body) return ''
  return sendStream(event, res.body)
})
