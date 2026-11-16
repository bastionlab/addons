/** one ≤8 MB chunk of an upload (raw body); the agent appends it and renames the file after the last one */
export default defineEventHandler(async (event) => {
  const q = getQuery(event)
  const data = await readRawBody(event, false)
  if (data && data.length > 8 * 2 ** 20) throw createError({ statusCode: 413, statusMessage: 'chunk too large' })
  const body = { root: String(q.root ?? 'files'), p: String(q.p ?? ''), name: String(q.name ?? ''), id: String(q.id ?? ''), offset: Number(q.offset), final: q.final === '1', data: (data ?? Buffer.alloc(0)).toString('base64') }
  return agent(event, '/files/upload', { method: 'POST', body, timeout: 120_000 })
})
