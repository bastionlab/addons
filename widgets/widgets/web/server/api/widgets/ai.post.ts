/** "Describe a widget": start a Claude job for { ask, base?, id }; owner only, it uses the Claude plan */
export default defineEventHandler(async (event) => {
  requireRole(event, 'owner')
  const b = await readBody(event)
  const ask = String(b?.ask ?? '').trim()
  if (!ask) throw bad(400, 'Describe the widget first')
  const h: Record<string, string> = {}
  for (const [k, v] of Object.entries(event.node.req.headers)) if (typeof v === 'string' && !['content-length', 'content-type', 'accept-encoding', 'connection'].includes(k)) h[k] = v
  const f = (p: string) => $fetch<any>(p, { headers: h, timeout: 8000, retry: 0 }).catch(() => null)
  const [o, t, n] = await Promise.all([f('/api/overview'), f('/api/chat-tasks'), f('/api/notes')])
  return widgetAiStart(ask, b?.base, {
    services: (o?.services ?? []).map((s: any) => String(s.name)).slice(0, 60),
    tasks: (t?.tasks ?? []).map((x: any) => ({ id: String(x.id), title: String(x.title) })).slice(0, 40),
    notes: (n?.notes ?? []).slice(0, 40).map((x: any) => ({ id: Number(x.id), title: String(x.title || x.body || '').slice(0, 50) })),
  })
})
