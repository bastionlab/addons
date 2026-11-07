/** benchmark ranking of models (llm-stats.com scores, cached daily by the agent) + fit and speed on this box */
export default defineEventHandler(event => agent(event, '/ai/compare'))
