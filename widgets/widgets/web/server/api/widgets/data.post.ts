/** { def } → { value, label?, at }: validates the definition, then reads its source (owner only) */
export default defineEventHandler(async (event) => {
  requireRole(event, 'owner')
  const body = await readBody(event)
  const d = parseDef(body?.def, true)
  if (d.look === 'component') {
    // a pack's component fetches nothing through here; it must still belong to an installed pack
    if (!widgetPacks().some(p => p.pack === d.pack && p.defs.some(x => x.id === d.id))) throw bad(404, 'pack not installed')
    return { value: null, at: Date.now() }
  }
  if (d.look === 'button') return { value: null, at: Date.now() }
  return widgetValue(event, d)
})
