/** { q, a } of a finished turn → { facts: string[] } worth remembering (at most 3, suggestions only: the owner confirms) */
export default defineEventHandler(async (event) => {
  const b = (await readBody(event)) ?? {}
  const q = String(b.q ?? '').slice(0, 1500), a = String(b.a ?? '').slice(0, 1500)
  if (!q.trim() || !a.trim()) return { facts: [] }
  const have = listFacts().slice(0, 40).map(f => `- ${f.text}`).join('\n')
  try {
    const raw = await ollamaChat([
      { role: 'system', content: 'You pick facts worth remembering from a chat between a homelab owner and an assistant. Only DURABLE facts about the owner (preferences, habits, devices, how he wants answers) or about his homelab (hosts, services, setup choices). Never task details, one-off questions, or things only true for this conversation. Each fact is one short, self-contained sentence. An empty list is the normal answer. Skip anything already remembered:\n' + (have || '(nothing yet)') + '\nAnswer JSON {"facts": ["..."]} with at most 3 facts.' },
      { role: 'user', content: `Owner: ${q}\n\nAssistant: ${a}` },
    ], { type: 'object', properties: { facts: { type: 'array', items: { type: 'string' }, maxItems: 3 } }, required: ['facts'] })
    const facts = (Array.isArray(JSON.parse(raw).facts) ? JSON.parse(raw).facts : []).map(cleanFact).filter((f: string) => f.length >= 8 && !isKnownFact(f)).slice(0, 3)
    return { facts }
  } catch { return { facts: [] } } // model busy or unreachable: no suggestion
})
