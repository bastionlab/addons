export default defineEventHandler(async (event) => {
  const action = getRouterParam(event, 'action')
  if (action !== 'revoke' && action !== 'delete') throw createError({ statusCode: 404 })
  const { id } = (await readBody(event)) ?? {}
  return shareCtl(`/${action}`, { id: String(id) })
})
