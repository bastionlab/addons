/** the marketplace's designs (`designs` in its index.json, via the agent that holds the GitHub token); ?fresh=1 skips the cache */
let cache: { at: number, list: any[] } | null = null

export default defineEventHandler(async (event) => {
  const fresh = getQuery(event).fresh === '1'
  if (!fresh && cache && Date.now() - cache.at < 10 * 60_000) return { designs: cache.list }
  const { agentUrl, agentToken } = useRuntimeConfig()
  const got = await upstream<any>('agent', agentUrl, agentToken, `/marketplace/index${fresh ? '?fresh=1' : ''}`, 20_000).catch(() => null)
  const raw = got?.designs ?? (useRuntimeConfig().marketplaceLocal as any)?.designs ?? []
  const list = (Array.isArray(raw) ? raw : []).filter((d: any) => d?.slug && d?.name).map((d: any) => ({
    slug: String(d.slug), name: String(d.name).slice(0, 40), author: String(d.author ?? ''), tokens: cleanTokens(d.tokens), updated: d.updated ?? null,
  }))
  if (got) cache = { at: Date.now(), list }
  return { designs: list }
})
