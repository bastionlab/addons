/** every share link + whether Tailscale Funnel is serving the public side (:8443) */
export default defineEventHandler(async () => {
  const r = await shareCtl<{ links: any[], funnel: { on: boolean, host: string | null } }>('/links')
  const base = `https://${r.funnel.host || `dash.${cfg().tailnet}`}:8443`
  return { funnel: r.funnel.on, base, links: r.links.map(l => ({ ...l, url: `${base}/s/${l.token}` })) }
})
