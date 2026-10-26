/** use a design: { pick: 'p:<built-in>' | 'd:<id>' } */
export default defineEventHandler(async (event) => {
  const uid = uidOf(event)
  setPick(uid, String((await readBody(event))?.pick ?? ''))
  return { pick: pickOf(uid), tokens: activeTokens(uid) }
})
