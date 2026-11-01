/** free homebrew to add with one tap (Homebrew Hub + Retrobrews), refreshed daily on the host */
export default defineEventHandler(event => agent(event, '/retro/catalog'))
