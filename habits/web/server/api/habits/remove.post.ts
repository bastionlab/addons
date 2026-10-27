/** delete a habit (its checks stay in the database) */
export default defineEventHandler(async event => removeHabit((await readBody(event))?.id))
