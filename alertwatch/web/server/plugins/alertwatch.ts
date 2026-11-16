// Alert watch's worker (utils/alertwatch.ts): once a minute, look for newly opened host alerts.
// LEARN_WORKER=0 (scratch/test builds) keeps it from starting Claude turns through the real agent
export default defineNitroPlugin(() => {
  if (process.env.LEARN_WORKER === '0') return
  setTimeout(() => tickAlertwatch().catch(() => {}), 20_000)
  setInterval(() => tickAlertwatch().catch(() => {}), 60_000)
})
