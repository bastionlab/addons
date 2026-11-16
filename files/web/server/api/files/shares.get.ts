/** the share links plus the public base URL (the same Funnel host the Dev add-on's share links use) */
export default defineEventHandler(async (event) => {
  const r = await agent<{ shares: any[] }>(event, '/files/shares')
  const f = await $fetch<any>('http://127.0.0.1:3101/links').then(d => d.funnel).catch(() => null)
  const base = `https://${f?.host || `dash.${cfg().tailnet}`}:8443`
  return { base, funnel: f?.on ?? null, shares: r.shares.map(s => ({ ...s, url: `${base}/f/${s.token}` })) }
})
