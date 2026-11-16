/** { job, model } → the new map; the agent validates both */
export default defineEventHandler(async (event) => {
  const b = (await readBody(event)) ?? {}
  return agent(event, '/ai/jobs', { method: 'POST', body: { job: String(b.job ?? ''), model: String(b.model ?? '') } })
})
