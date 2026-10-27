import { createReadStream, existsSync } from 'node:fs'
import { join } from 'node:path'

/** a design image (any signed-in viewer: shared designs show them to everyone); names are random, files never change */
export default defineEventHandler((event) => {
  const f = String(getRouterParam(event, 'file') ?? '')
  const m = /^[a-f0-9]{24}\.(png|jpe?g|webp|gif)$/.exec(f)
  if (!m || !existsSync(join(IMG_DIR, f))) throw createError({ statusCode: 404, statusMessage: 'Not found' })
  setHeader(event, 'Content-Type', IMG_MIME[m[1]!]!)
  setHeader(event, 'Cache-Control', 'private, max-age=31536000, immutable')
  setHeader(event, 'X-Content-Type-Options', 'nosniff')
  return sendStream(event, createReadStream(join(IMG_DIR, f)))
})
