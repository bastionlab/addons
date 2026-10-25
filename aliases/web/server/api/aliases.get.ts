/** the alias list + login state; DuckDuckGo is only ever called from the host (agent/duck_aliases.py) */
export default defineEventHandler(event => agent(event, '/aliases/list'))
