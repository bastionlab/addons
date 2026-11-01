/** a game, cover, BIOS or save: the agent's bytes piped straight through */
export default defineEventHandler(async (event) => {
  const q = getQuery(event)
  const kind = String(q.kind ?? 'rom')
  if (!['rom', 'cover', 'bios', 'srm', 'state'].includes(kind)) throw createError({ statusCode: 400, statusMessage: 'bad kind' })
  const { agentUrl, agentToken } = useRuntimeConfig(event)
  const qs = new URLSearchParams({ sys: String(q.sys ?? ''), name: String(q.name ?? ''), kind })
  const ctl = new AbortController()
  event.node.req.on('close', () => ctl.abort())
  const res = await fetch(`${agentUrl}/retro/file?${qs}`, { headers: { Authorization: `Bearer ${agentToken}` }, signal: ctl.signal }).catch((e: any) => {
    throw createError({ statusCode: 502, statusMessage: `agent: ${e?.message}` })
  })
  if (!res.ok || !res.body) throw createError({ statusCode: res.status === 404 ? 404 : res.status === 400 ? 400 : 502, statusMessage: (await res.text()).slice(0, 200) || 'not found' })
  const image = kind === 'cover'
  const ext = String(q.name ?? '').split('.').pop()?.toLowerCase()
  setResponseHeaders(event, {
    'Content-Type': image ? `image/${ext === 'jpg' ? 'jpeg' : ext}` : 'application/octet-stream',
    'Content-Length': res.headers.get('content-length') ?? '',
    'Cache-Control': image || kind === 'rom' ? 'private, max-age=86400' : 'no-store',
    'Cross-Origin-Resource-Policy': 'same-origin',
  })
  return sendStream(event, res.body)
})
