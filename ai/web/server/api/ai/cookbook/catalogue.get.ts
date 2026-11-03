/** what fits the 3060, ranked: ?ctx= is the context length the KV cache is sized for (clamped by the agent) */
export default defineEventHandler((event) => {
  const n = Math.round(Number(getQuery(event).ctx))
  return agent(event, `/ai/catalogue?ctx=${Number.isFinite(n) ? Math.min(Math.max(n, 2048), 131072) : 8192}`)
})
