export default defineEventHandler(event => agent(event, '/retro/info', { query: { id: String(getQuery(event).id ?? '') } }))
