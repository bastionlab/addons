/** { items: [{ id, title, q }] (or ids: the stored chats), folders: [existing] } → { id: folder } (suggestions only) */
export default defineEventHandler(async (event) => {
  const b = (await readBody(event)) ?? {}
  const okId = (v: any) => typeof v === 'string' && /^[\w-]{1,40}$/.test(v)
  const items: { id: string, title: string, q: string }[] = []
  for (const i of Array.isArray(b.items) ? b.items.slice(0, 60) : []) {
    if (okId(i?.id)) items.push({ id: i.id, title: String(i.title ?? ''), q: String(i.q ?? '') })
  }
  for (const id of (Array.isArray(b.ids) ? b.ids.slice(0, 60) : []).filter(okId)) {
    if (items.some(i => i.id === id)) continue
    const c = chatById(id)
    if (c && !c.folder) items.push({ id, title: String(c.title ?? ''), q: String(c.turns?.[0]?.q ?? '') })
  }
  const folders = (Array.isArray(b.folders) ? b.folders : []).map(String)
  return await sortChats(items, folders)
})
