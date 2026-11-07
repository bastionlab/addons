/** what the builder can offer to pick from: services, scheduled tasks, notes (best effort: any can be missing) */
export default defineEventHandler(async (event) => {
  requireRole(event, 'owner')
  const h: Record<string, string> = {}
  for (const [k, v] of Object.entries(event.node.req.headers)) if (typeof v === 'string' && !['content-length', 'content-type', 'accept-encoding', 'connection'].includes(k)) h[k] = v
  const f = (p: string) => $fetch<any>(p, { headers: h, timeout: 8000, retry: 0 }).catch(() => null)
  const [o, t, n] = await Promise.all([f('/api/overview'), f('/api/chat-tasks'), f('/api/notes')])
  return {
    services: (o?.services ?? []).map((s: any) => String(s.name)).slice(0, 80),
    tasks: (t?.tasks ?? []).map((x: any) => ({ id: String(x.id), title: String(x.title) })).slice(0, 80),
    notes: (n?.notes ?? []).filter((x: any) => x.state !== 'archived').slice(0, 80).map((x: any) => ({ id: Number(x.id), title: String(x.title || x.body || '').slice(0, 60) })),
  }
})
