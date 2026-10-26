/** delete one of your designs (the owner may remove anyone's); people using it go back to the stock look */
export default defineEventHandler((event) => {
  deleteDesign(uidOf(event), Number(getRouterParam(event, 'id')), roleOf(event) === 'owner')
  return { ok: true }
})
