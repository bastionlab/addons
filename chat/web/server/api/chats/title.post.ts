/** { q, a?, prior? } → { title } (3-6 words from the local model) or { title: null } when it fails */
export default defineEventHandler(async (event) => {
  const b = (await readBody(event)) ?? {}
  const q = String(b.q ?? '').slice(0, 800), a = String(b.a ?? '').slice(0, 800)
  if (!q.trim()) return { title: null }
  try {
    const raw = await ollamaChat([
      { role: 'system', content: 'Name this chat in 3 to 6 words, in the language of the question. The question decides the topic; the answer is only context. Ignore an answer that merely asks the user to switch on Auto mode, asks for permission, or refuses. If the question mentions a note or feature by name in quotes, name the chat after that. Name the topic or goal, not a copy of the question. No quotes, no emoji, no trailing period. Output only the title.' },
      { role: 'user', content: `${b.prior ? `Current title: ${String(b.prior).slice(0, 80)}\n` : ''}Question: ${q}${a ? `\n\nAnswer (excerpt): ${a}` : ''}` },
    ])
    const title = raw.replace(/["“”„«»`]/g, '').replace(/\s+/g, ' ').trim().replace(/^['’]+|['’]+$/g, '').replace(/[.!?:;,\s]+$/, '').slice(0, 60).trim()
    return { title: title || null }
  } catch { return { title: null } }
})
