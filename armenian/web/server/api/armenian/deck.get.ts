/** the whole deck (static): the browse grid and search work on it in the page */
export default defineEventHandler((event) => {
  setHeader(event, 'cache-control', 'no-cache')
  return ARM_DECK
})
