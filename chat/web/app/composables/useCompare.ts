import type { Chat } from '~/composables/useChats'
import type { Turn } from '~/composables/useAsk'

/**
 * Compare (idea from Odysseus): one question to up to three models side by side — Claude models (each its own
 * read-only one-off turn on pve, chat id `<chat>x<n>`) and/or a local model on the 3060. Panes show as A/B/C until
 * the owner picks the best; then the names come out and the pick counts towards a per-device scoreboard.
 */
export interface Pick { engine: 'claude' | 'local', model: string }
type Pane = NonNullable<Turn['cmp']>[number]
const PICKS = 'chat.compare.picks', SCORE = 'chat.compare.score'

export function useCompare(claude: ReturnType<typeof useClaude>, save: () => void) {
  const { models } = useAskSettings()
  const picks = ref<Pick[]>([])
  const score = ref<Record<string, number>>({})
  onMounted(() => {
    try { picks.value = JSON.parse(localStorage.getItem(PICKS) || '[]') } catch {}
    try { score.value = JSON.parse(localStorage.getItem(SCORE) || '{}') } catch {}
  })
  // default: two Claude models + whatever local model is warm
  const active = computed<Pick[]>(() => picks.value.length ? picks.value : [
    { engine: 'claude', model: 'sonnet' }, { engine: 'claude', model: 'haiku' },
    ...(models.value?.length ? [{ engine: 'local' as const, model: (models.value.find((m: any) => m.warm) ?? models.value[0]).name }] : []),
  ])
  function setPicks(p: Pick[]) {
    picks.value = p.slice(0, 3)
    try { localStorage.setItem(PICKS, JSON.stringify(picks.value)) } catch {}
  }

  async function local(p: Pane, q: string) {
    try {
      const res = await fetch('/api/ai/ask', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ q, model: p.label, think: false, web: true, scope: 'chat', history: [] }),
      })
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`)
      const reader = res.body.getReader(), dec = new TextDecoder()
      let buf = ''
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        buf += dec.decode(value, { stream: true })
        const lines = buf.split('\n')
        buf = lines.pop()!
        for (const line of lines) {
          let j: any
          try { j = JSON.parse(line) } catch { continue }
          if (j.c) p.a += j.c
          if (j.error) p.error = j.error
          if (j.done) { p.model = j.model; p.tps = j.tps }
        }
      }
    } catch (e: any) { p.error = e?.message || 'failed' } finally { p.busy = false; p.fin = true }
  }

  async function remote(c: Chat, p: Pane, n: number, q: string) {
    try {
      const r = await $fetch<{ turn?: string }>('/api/claude/send', {
        method: 'POST', body: { chat: `${c.id}x${n}`, session: crypto.randomUUID(), prompt: q, auto: false, model: p.label, effort: 'medium', team: false, push: false },
      })
      if (!r.turn) throw new Error('busy')
      p.ct = r.turn
      save()
      await claude.attach(p)
    } catch (e: any) { p.error = e?.data?.statusMessage || e?.message || 'failed'; p.busy = false; p.fin = true }
  }

  async function compare(c: Chat, q: string) {
    q = q.trim()
    if (!q || c.turns.some(t => t.busy)) return
    const panes: Pane[] = active.value.map((p, i) => ({ key: 'ABC'[i]!, engine: p.engine, label: p.model, q, a: '', r: '', tools: [], busy: true, at: Date.now() }))
    c.turns.push({ q, a: '', r: '', at: Date.now(), busy: true, model: 'compare', cmp: panes })
    const t = c.turns.at(-1)!
    save()
    await Promise.all(t.cmp!.map((p, i) => p.engine === 'claude' ? remote(c, p, i, q) : local(p, q)))
    t.busy = false
    t.fin = true
    save()
  }

  function vote(t: Turn, key: string) {
    if (t.vote || t.busy) return
    t.vote = key
    const p = t.cmp?.find(x => x.key === key)
    if (p) score.value[p.label] = (score.value[p.label] ?? 0) + 1
    try { localStorage.setItem(SCORE, JSON.stringify(score.value)) } catch {}
    save()
  }

  return { compare, vote, picks: active, setPicks, score }
}
