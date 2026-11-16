export default defineEventHandler(event => agent(event, '/gcal/events', { query: getQuery(event) }))
