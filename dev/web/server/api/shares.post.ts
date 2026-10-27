/** new share link for a project's preview port; the target is looked up here, never taken from the browser */
export default defineEventHandler(async (event) => {
  const { vmid, path, port, ttl, once } = (await readBody(event)) ?? {}
  const boxes = await agent<any[]>(event, '/projects')
  const box = boxes.find(b => b.vmid === Number(vmid))
  const p = box?.projects?.find((x: any) => x.path === path)
  if (!box?.ip || !p) throw createError({ statusCode: 400, statusMessage: 'unknown project' })
  const ports: number[] = [...(p.ports ?? []), ...(p.urls ?? []).map((u: any) => u.port)]
  if (!ports.includes(Number(port))) throw createError({ statusCode: 400, statusMessage: `port ${port} is not one of ${p.name}'s` })
  const secs = Number(ttl)
  if (!Number.isFinite(secs) || secs < 0 || secs > 90 * 86400) throw createError({ statusCode: 400, statusMessage: 'bad expiry' })
  return shareCtl('/links', { target: `${box.ip}:${Number(port)}`, label: p.name, project: { vmid: box.vmid, path, port: Number(port) }, ttl: secs, once: !!once })
})
