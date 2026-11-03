/** the model each job uses ('' = the warm model) */
export default defineEventHandler(event => agent(event, '/ai/jobs'))
