/** add (label, path, writable) or remove (id) a root */
export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  if (b?.id) return agent(event, '/files/roots/remove', { method: 'POST', body: { id: String(b.id) } })
  return agent(event, '/files/roots/add', { method: 'POST', body: { label: String(b?.label ?? ''), path: String(b?.path ?? ''), writable: b?.writable === true } })
})
