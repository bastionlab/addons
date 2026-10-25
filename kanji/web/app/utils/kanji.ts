/** on'yomi are written in katakana, like in every dictionary */
export const kata = (s: string) => s.replace(/[ぁ-ゖ]/g, c => String.fromCharCode(c.charCodeAt(0) + 0x60))

/** "ひと.つ" → stem + okurigana, "-び" → suffix marker kept */
export function kun(r: string) {
  const [stem, oku = ''] = r.split('.')
  return { stem: stem!, oku }
}

// 0 new, 1 learning, 2 young, 3 mature (server: overview().status)
export const STATUS = ['New', 'Learning', 'Young', 'Mature'] as const

export const LEVELS = [5, 4, 3, 2, 1] as const

export type KanjiCard = { k: string, n: number, s: number, m: string[], on: string[], kun: string[], w: [string, string, string][] }

/** the deck is static: fetch it once per app load */
export function useKanjiDeck() {
  const deck = useState<KanjiCard[] | null>('kanji:deck', () => null)
  if (!deck.value && import.meta.client) $fetch<KanjiCard[]>('/api/kanji/deck').then(d => (deck.value = d)).catch(() => {})
  return deck
}

export type Strokes = { paths: string[], nums: number[][] }
/** stroke data per kanji, kept for the app's lifetime so the pad never waits twice for the same kanji */
const STROKES = new Map<string, Strokes>()
const PENDING = new Map<string, Promise<Strokes>>()
export const cachedStrokes = (k: string) => STROKES.get(k) ?? null
/** one retry: an app rebuild briefly answers 502 */
export function loadStrokes(k: string): Promise<Strokes> {
  if (STROKES.has(k)) return Promise.resolve(STROKES.get(k)!)
  if (!PENDING.has(k)) {
    const get = () => $fetch<Strokes>('/api/kanji/strokes', { query: { k } })
    PENDING.set(k, get().catch(() => new Promise(r => setTimeout(r, 1500)).then(get))
      .then((d) => { STROKES.set(k, d); return d })
      .finally(() => PENDING.delete(k)))
  }
  return PENDING.get(k)!
}
/** warm the cache for every kanji in a word (the pad moves on without a Loading… between them) */
export const prefetchStrokes = (s: string) => { for (const c of new Set(s)) if (/[一-鿿]/.test(c)) loadStrokes(c).catch(() => {}) }
