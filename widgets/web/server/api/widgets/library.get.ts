/** installed widget packs (add-ons with kind: widget) and their validated definitions */
export default defineEventHandler((event) => {
  requireRole(event, 'owner')
  return { packs: widgetPacks() }
})
