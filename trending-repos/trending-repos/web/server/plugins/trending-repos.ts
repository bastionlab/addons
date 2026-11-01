// the Trending tab's daily refresh; TRENDING_REPOS_WORKER=0 keeps a scratch/test build away from GitHub and the models
export default defineNitroPlugin(() => {
  if (process.env.TRENDING_REPOS_WORKER === '0') return
  setTimeout(maybeRefresh, 60_000)
  setInterval(maybeRefresh, 15 * 60_000)
})
