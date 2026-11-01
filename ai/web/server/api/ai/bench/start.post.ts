/** start the benchmark (it unloads the warm model for a while and puts it back) */
export default defineEventHandler(event => agent(event, '/ai/bench/start', { method: 'POST', body: {} }))
