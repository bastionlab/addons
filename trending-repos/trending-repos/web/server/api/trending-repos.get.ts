/** one list (?state=new|saved|dismissed), the counts and the refresh status */
export default defineEventHandler((event) => {
  const s = String(getQuery(event).state ?? 'new')
  const state = ['new', 'saved', 'dismissed'].includes(s) ? s : 'new'
  return { repos: listRepos(state), counts: counts(), status: { ...status(), busy: refreshing() } }
})
