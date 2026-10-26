/** paint a design: the core's CSS tokens as inline vars on <html>, so every page and add-on follows; null = stock look */
export const DESIGN_COLORS = ['bg', 'panel', 'panel-2', 'line', 'line-2', 'text', 'muted', 'faint', 'accent', 'ok', 'warn', 'bad', 'track', 'claude', 'term-bg', 'term-fg'] as const
export type DesignTokens = Record<string, any>
const CACHE = 'designs:active'

export function applyDesign(t: DesignTokens | null, remember = true) {
  if (typeof document === 'undefined') return
  const s = document.documentElement.style
  for (const k of DESIGN_COLORS) t?.[k] ? s.setProperty(`--${k}`, t[k]) : s.removeProperty(`--${k}`)
  const softs: [string, number][] = [['accent', 12], ['ok', 12], ['warn', 12], ['bad', 13]]
  for (const [k, pct] of softs) t ? s.setProperty(`--${k}-soft`, `color-mix(in srgb, var(--${k}) ${pct}%, transparent)`) : s.removeProperty(`--${k}-soft`)
  if (t && Number.isFinite(t.radius)) {
    s.setProperty('--radius', `${t.radius}px`)
    s.setProperty('--radius-sm', `${Math.round(t.radius * 2 / 3)}px`)
  } else { s.removeProperty('--radius'); s.removeProperty('--radius-sm') }
  t?.scheme ? s.setProperty('color-scheme', t.scheme) : s.removeProperty('color-scheme')
  const meta = document.querySelector('meta[name="theme-color"]')
  if (meta) {
    if (!meta.getAttribute('data-stock')) meta.setAttribute('data-stock', meta.getAttribute('content') || '')
    meta.setAttribute('content', t?.bg || meta.getAttribute('data-stock') || '')
  }
  if (remember) {
    try { t ? localStorage.setItem(CACHE, JSON.stringify(t)) : localStorage.removeItem(CACHE) } catch {}
  }
}

export function cachedDesign(): DesignTokens | null {
  try { return JSON.parse(localStorage.getItem(CACHE) || 'null') } catch { return null }
}

/** a design as a code to paste into another Bastion: base64url of { n: name, t: tokens } */
export function designCode(name: string, tokens: DesignTokens) {
  const b = new TextEncoder().encode(JSON.stringify({ v: 1, n: name, t: tokens }))
  return 'bastion-design:' + btoa(String.fromCharCode(...b)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

/** the other way; the server re-checks every token before it is stored */
export function readDesignCode(code: string): { name: string, tokens: DesignTokens } | null {
  try {
    const s = code.trim().replace(/^bastion-design:/, '').replace(/-/g, '+').replace(/_/g, '/')
    const j = JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(s), c => c.charCodeAt(0))))
    return j?.t && typeof j.t === 'object' ? { name: String(j.n || 'Imported').slice(0, 40), tokens: j.t } : null
  } catch { return null }
}
