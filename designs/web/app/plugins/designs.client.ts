/** paint this person's design: the last one at once (no flash of the stock look), then whatever the server says */
export default defineNuxtPlugin(() => {
  applyDesign(cachedDesign(), false)
  $fetch<{ tokens: DesignTokens | null }>('/api/designs/active').then(r => applyDesign(r.tokens)).catch(() => {})
})
