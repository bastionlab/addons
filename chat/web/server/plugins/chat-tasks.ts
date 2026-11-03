// scheduled chat tasks (utils/chatTasks.ts): once a minute, start the ones that are due.
// LEARN_WORKER=0 (scratch/test builds) keeps it from starting Claude turns through the real agent
export default defineNitroPlugin(() => {
  if (process.env.LEARN_WORKER === '0') return
  setInterval(() => tickTasks().catch(() => {}), 60_000)
})
