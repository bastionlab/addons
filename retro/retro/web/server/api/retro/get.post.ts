/** download one catalogue game into the library */
export default defineEventHandler(async (event) => {
  const b = (await readBody(event)) ?? {}
  return agent(event, '/retro/get', { method: 'POST', body: { id: String(b.id ?? '') } })
})
