// the Daily briefing's worker: once a minute, see whether today's briefing is due (after the set time, none yet)
// BRIEFING_WORKER=0 keeps a scratch/test build from reading real data or asking the model
export default defineNitroPlugin(() => {
  if (process.env.BRIEFING_WORKER === '0') return
  setTimeout(tick, 20_000)
  setInterval(tick, 60_000)
})

async function tick() {
  try {
    if (addonsOff().includes('briefing')) return
    await runBriefing()
  } catch (e: any) {
    console.warn(`[briefing] worker: ${e?.message}`)
  }
}
