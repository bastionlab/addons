/** marks a suggestion as seen so Discover stops showing it; "Seen it" on a series also watches it for new seasons/episodes, dismiss: true does not */
export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  return agent(event, '/media/discover/seen', { method: 'POST', body: { kind: String(b?.kind ?? ''), tmdbId: String(b?.tmdbId ?? ''), dismiss: !!b?.dismiss } })
})
