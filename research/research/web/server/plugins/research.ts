// the Research tab's worker: every 5 s, start the next queued question if nothing is running
// RESEARCH_WORKER=0 keeps a scratch/test build away from the real models and search
export default defineNitroPlugin(() => {
  if (process.env.RESEARCH_WORKER === '0') return
  setInterval(tick, 5_000)
})
