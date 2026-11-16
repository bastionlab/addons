/** what is in VRAM right now, by process owner */
export default defineEventHandler(event => agent(event, '/ai/vram'))
