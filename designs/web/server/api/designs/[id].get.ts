/** one design you may see (yours or shared); the host's design-publish reads it from inside the CT */
export default defineEventHandler((event) => {
  const d = getDesign(Number(getRouterParam(event, 'id')))
  if (!d || !(event.context.inside || d.uid === uidOf(event) || d.shared)) throw createError({ statusCode: 404, statusMessage: 'Not found' })
  return { id: d.id, name: d.name, tokens: d.tokens, css: d.css, skin: d.skin }
})
