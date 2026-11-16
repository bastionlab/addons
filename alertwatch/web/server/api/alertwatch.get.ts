/** open alerts, the log and what Claude found for each. The add-on's `roles:` covers /api/alertwatch/*; the owner check is explicit too. */
export default defineEventHandler((event) => {
  requireRole(event, 'owner')
  return alertwatchView()
})
