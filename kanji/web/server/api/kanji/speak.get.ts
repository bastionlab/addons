export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const q = typeof query.q === 'string' ? query.q.normalize('NFC') : ''
  if (!kjTtsAllowed(q)) throw createError({ statusCode: 404, statusMessage: 'Not in the deck' })
  let audio: Buffer
  try { audio = await kjTtsGet(q) } catch (e: any) { throw createError({ statusCode: 502, statusMessage: e?.message || 'Speech unavailable' }) }
  setHeader(event, 'content-type', 'audio/mpeg')
  setHeader(event, 'cache-control', 'private, max-age=31536000, immutable')
  return audio
})
