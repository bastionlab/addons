// proposals only, nothing is saved; the page's Accept calls categories-save
export default defineEventHandler(event => agent(event, '/mail/categories/suggest', { method: 'POST', body: {}, timeout: 180_000 }))
