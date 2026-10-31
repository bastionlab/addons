import { createHash } from 'node:crypto'
import { mkdir, readFile, rename, writeFile } from 'node:fs/promises'
import { join } from 'node:path'
import { DECK } from './kanji'

/**
 * Read-out audio (2026-10-27): Google Translate TTS, fetched once per distinct text and kept on disk in CT 104
 * (<NOTES_DIR>/tts/ja/<sha1>.mp3), so every later play is a file read. Only kana readings from the deck and its
 * example words can be asked for: this is not a proxy.
 */
const KJ_TTS_DIR = join(process.env.NOTES_DIR || '/var/lib/dash', 'tts', 'ja')
const KJ_TTS_OK = new Set<string>()
for (const c of DECK) {
  for (const r of [...c.on, ...c.kun]) { const t = r.replace(/[.-]/g, ''); if (t) KJ_TTS_OK.add(t) }
  for (const [w, r] of c.w) { KJ_TTS_OK.add(w); KJ_TTS_OK.add(r) }
}
const kjTtsFlight = new Map<string, Promise<Buffer>>()

export const kjTtsAllowed = (q: string) => !!q && q.length <= 120 && KJ_TTS_OK.has(q)

async function kjTtsFetch(q: string): Promise<Buffer> {
  const r = await fetch(`https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=ja&q=${encodeURIComponent(q)}`, {
    headers: { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36', 'Referer': 'https://translate.google.com/' },
    signal: AbortSignal.timeout(8000),
  })
  const buf = Buffer.from(await r.arrayBuffer())
  if (!r.ok || !(r.headers.get('content-type') || '').includes('audio/mpeg') || buf.length <= 500)
    throw new Error(`Google TTS ${r.status} ${r.headers.get('content-type') || ''} ${buf.length} B`)
  return buf
}

/** cached mp3 for an allowed text; concurrent asks for the same text share one fetch */
export async function kjTtsGet(q: string): Promise<Buffer> {
  const file = join(KJ_TTS_DIR, `${createHash('sha1').update(q).digest('hex')}.mp3`)
  try { return await readFile(file) } catch {}
  let p = kjTtsFlight.get(q)
  if (!p) {
    p = kjTtsFetch(q).then(async (b) => {
      await mkdir(KJ_TTS_DIR, { recursive: true })
      await writeFile(`${file}.tmp`, b)
      await rename(`${file}.tmp`, file)
      return b
    }).finally(() => kjTtsFlight.delete(q))
    kjTtsFlight.set(q, p)
  }
  return p
}
