export interface Fact { id: number, text: string, src: string, at: number, pinned: boolean }

/** chat memory (server/utils/memory.ts): the facts live on the server, this is the shared list + the few writes */
export function useMemory() {
  const facts = useState<Fact[]>('chat.memory', () => [])
  const count = computed(() => facts.value.length)
  const put = (r: any) => { if (Array.isArray(r?.facts)) facts.value = r.facts; return r }
  const post = (body: any) => $fetch<any>('/api/memory/action', { method: 'POST', body }).then(put)
  return {
    facts, count,
    load: () => $fetch<any>('/api/memory').then(put).catch(() => {}),
    add: (text: string, src = '') => post({ action: 'add', text, src }),
    edit: (id: number, text: string) => post({ action: 'edit', id, text }),
    pin: (id: number, pinned: boolean) => post({ action: 'pin', id, pinned }),
    del: (id: number) => post({ action: 'delete', id }),
    suggest: (q: string, a: string): Promise<string[]> => $fetch<any>('/api/memory/suggest', { method: 'POST', body: { q: q.slice(0, 1500), a: a.slice(0, 1500) } }).then(r => (Array.isArray(r?.facts) ? r.facts : [])).catch(() => []),
  }
}
