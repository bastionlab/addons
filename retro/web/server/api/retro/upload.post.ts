/** one ≤8 MB chunk of a game file (raw body); the agent appends it and renames the file after the last one */
export default defineEventHandler(async (event) => {
  const q = getQuery(event)
  const data = await readRawBody(event, false)
  if (!data || data.length > 8 * 2 ** 20) throw createError({ statusCode: 400, statusMessage: 'bad chunk' })
  const body = { sys: String(q.sys ?? ''), name: String(q.name ?? ''), kind: q.kind === 'bios' ? 'bios' : 'rom', offset: Number(q.offset), total: Number(q.total), data: data.toString('base64') }
  return upstream('agent', useRuntimeConfig(event).agentUrl, useRuntimeConfig(event).agentToken, '/retro/upload', 120_000, { method: 'POST', body })
})
