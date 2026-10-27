/** mark a habit done / not done on a day: { habit, day: 'YYYY-MM-DD', done } */
export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  return setCheck(b?.habit, b?.day, b?.done === true)
})
