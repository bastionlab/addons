/** create or edit a habit: { id?, title, freq: daily|weekly|days, days: number[] (0 = Monday) } */
export default defineEventHandler(async event => saveHabit(await readBody(event)))
