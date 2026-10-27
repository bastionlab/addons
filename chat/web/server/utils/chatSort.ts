/**
 * Auto-sort chats into sidebar folders with the local model: title + first question → one of the existing folders
 * or a new short name (seeded from SEEDS), at most MAX_FOLDERS in total. Only suggests; the client sets `folder`.
 */
export const SEEDS = ['Server', 'Dev', 'Money', 'Media', 'Ideas', 'Learning', 'Other']
const MAX_FOLDERS = 8

export const cleanFolder = (v: any) => String(v ?? '').replace(/[\r\n]+/g, ' ').trim().slice(0, 24).trim()

export async function sortChats(items: { id: string, title: string, q: string }[], existing: string[]) {
  const have = [...new Set(existing.map(cleanFolder).filter(Boolean))]
  const out: Record<string, string> = {}
  for (const it of items) {
    const room = have.length < MAX_FOLDERS
    const pool = [...have, ...(room ? SEEDS.filter(s => !have.some(h => h.toLowerCase() === s.toLowerCase())) : [])]
    const schema = { type: 'object', properties: { folder: room ? { type: 'string' } : { type: 'string', enum: have } }, required: ['folder'] }
    try {
      const raw = await ollamaChat([
        { role: 'system', content: `You file chat conversations into folders. Existing folders: ${have.join(', ') || '(none)'}. Prefer an existing folder that fits. Otherwise pick a new one, preferably from: ${pool.join(', ')}; or a short name of 1-2 words. Answer JSON {"folder": "..."}.` },
        { role: 'user', content: `Title: ${it.title.slice(0, 100)}\nFirst question: ${it.q.slice(0, 300)}` },
      ], schema)
      let f = cleanFolder(JSON.parse(raw).folder)
      if (!f) continue
      const known = have.find(h => h.toLowerCase() === f.toLowerCase())
      if (known) f = known
      else if (!room) continue
      else have.push(f)
      out[it.id] = f
    } catch { /* model busy or unreachable: leave the chat unsorted */ }
  }
  return out
}
