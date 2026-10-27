/** put (add / change), del, or run a scheduled chat task now */
export default defineEventHandler(async (event) => {
  const b = (await readBody(event)) ?? {}
  if (b.op === 'put') return { task: putTask(b.task) }
  if (b.op === 'del') { dropTask(String(b.id)); return { ok: true } }
  if (b.op === 'run') return { task: await runTask(String(b.id)) }
  throw createError({ statusCode: 400, statusMessage: 'op is put, del or run' })
})
