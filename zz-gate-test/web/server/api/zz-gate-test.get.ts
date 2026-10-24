/** the page's data; anything on the host goes through the agent (agent/zz-gate-test.py), never a raw address */
export default defineEventHandler(event => agent(event, '/zz-gate-test/hello'))
