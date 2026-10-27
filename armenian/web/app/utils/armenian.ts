// 0 new, 1 learning, 2 young, 3 mature (server: overview().status)
export const STATUS = ['New', 'Learning', 'Young', 'Mature'] as const

export type ArmCard = { id: string, t: 'l' | 'w', g: number, hy: string, tr: string, en: string[], cat: string, ex: [string, string, string] | null }

/** the lowercase alphabet in order, plus the ligature և: the on-screen keyboard for typing answers */
export const LETTERS = [...'աբգդեզէըթժիլխծկհձղճմյնշոչպջռսվտրցւփքօֆ', 'և']

export const groupName = (g: number) => (g === 0 ? 'Alphabet' : `Pack ${g}`)

/** what the learner has to produce for a card: a letter's lowercase glyph, a word as written */
export const answerOf = (c: Pick<ArmCard, 't' | 'hy' | 'id'>) => (c.t === 'l' ? c.id.replace(/^w:/, '') : c.hy)
/** case, spacing and composition don't count */
export const norm = (s: string) => s.normalize('NFC').toLowerCase().replace(/\s+/g, ' ').trim()

/** the deck is static: fetch it once per app load */
export function useArmenianDeck() {
  const deck = useState<ArmCard[] | null>('armenian:deck', () => null)
  if (!deck.value && import.meta.client) $fetch<ArmCard[]>('/api/armenian/deck?v=2').then(d => (deck.value = d)).catch(() => {})
  return deck
}

