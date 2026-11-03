/** the remembered facts (pinned first, then newest) */
export default defineEventHandler(() => ({ facts: listFacts(), max: MEM_MAX_FACTS }))
