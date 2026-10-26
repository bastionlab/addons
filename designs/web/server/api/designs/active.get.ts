/** the look to paint for this person (null = stock), fetched by the app on every load */
export default defineEventHandler(event => ({ tokens: activeTokens(uidOf(event)) }))
