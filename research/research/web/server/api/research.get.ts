/** the list; ?id= returns one run with its report */
export default defineEventHandler((event) => {
  const id = Number(getQuery(event).id)
  if (id) {
    const r = getResearch(id)
    if (!r) throw createError({ statusCode: 404, statusMessage: 'no such run' })
    return r
  }
  return { runs: listResearch() }
})
