export default defineEventHandler(event => armCardInfo(String(getQuery(event).k ?? '').slice(0, 40)))
