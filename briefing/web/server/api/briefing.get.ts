/**
 * Today's briefing, when the next one is due and which sections would be read. Role gating: the add-on's `roles:`
 * (addon.yaml) already covers /api/briefing/*, since access.ts matches the add-on whose api/ folder names the prefix;
 * the owner check here is explicit as well because the briefing holds mail counts, calendar titles and alerts.
 */
export default defineEventHandler((event) => {
  requireRole(event, 'owner')
  return briefingView()
})
