/** paint a design: the core's CSS tokens as inline vars on <html>, so every page and add-on follows; null = stock look.
 *  applyLook adds the design's stylesheet and skin (core pieces render Skin<Name><Piece> components, useSkin). */
export const DESIGN_COLORS = ['bg', 'panel', 'panel-2', 'line', 'line-2', 'text', 'muted', 'faint', 'accent', 'ok', 'warn', 'bad', 'track', 'claude', 'term-bg', 'term-fg'] as const
export type DesignTokens = Record<string, any>
export type Look = { tokens: DesignTokens, css?: string, skin?: string }
const CACHE = 'designs:look'
const OFF = 'designs:off'

// the core's skin state (useState 'skin'), handed over by the plugin so clicks outside setup can switch it
let skinRef: { value: string } | null = null
export const bindSkin = (r: { value: string }) => (skinRef = r)

/** ?design=off on any URL: the stock look for this tab, a way out when a design hides what you need */
export function safeMode() {
  try {
    const q = new URLSearchParams(location.search).get('design')
    if (q === 'off') sessionStorage.setItem(OFF, '1')
    if (q === 'on') sessionStorage.removeItem(OFF)
    return sessionStorage.getItem(OFF) === '1'
  } catch { return false }
}

export function applyLook(l: Look | null, remember = true) {
  if (typeof document === 'undefined') return
  if (safeMode()) l = null
  applyDesign(l?.tokens ?? null)
  let st = document.getElementById('design-css') as HTMLStyleElement | null
  if (l?.css) {
    if (!st) { st = document.createElement('style'); st.id = 'design-css'; document.head.appendChild(st) }
    st.textContent = l.css
  } else st?.remove()
  const h = document.documentElement
  for (const c of [...h.classList]) if (c.startsWith('skin-')) h.classList.remove(c)
  if (l?.skin) h.classList.add(`skin-${l.skin}`)
  if (skinRef) skinRef.value = l?.skin ?? ''
  // framed apps (Habits) follow too: they get the look via postMessage from their page (window event, no import)
  ;(window as any).__bastionLook = l
  window.dispatchEvent(new CustomEvent('bastion:look'))
  if (remember) {
    try { l ? localStorage.setItem(CACHE, JSON.stringify(l)) : localStorage.removeItem(CACHE) } catch {}
  }
}

function applyDesign(t: DesignTokens | null) {
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
}

export function cachedLook(): Look | null {
  try { return JSON.parse(localStorage.getItem(CACHE) || 'null') } catch { return null }
}

/** a design as a code to paste into another Bastion: base64url of { n: name, t: tokens } */
export function designCode(name: string, l: Look) {
  const b = new TextEncoder().encode(JSON.stringify({ v: 2, n: name, t: l.tokens, c: l.css || undefined, s: l.skin || undefined }))
  return 'bastion-design:' + btoa(String.fromCharCode(...b)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

/** the other way; the server re-checks every token before it is stored */
export function readDesignCode(code: string): { name: string, tokens: DesignTokens, css: string, skin: string } | null {
  try {
    const s = code.trim().replace(/^bastion-design:/, '').replace(/-/g, '+').replace(/_/g, '/')
    const j = JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(s), c => c.charCodeAt(0))))
    return j?.t && typeof j.t === 'object' ? { name: String(j.n || 'Imported').slice(0, 40), tokens: j.t, css: String(j.c ?? ''), skin: String(j.s ?? '') } : null
  } catch { return null }
}
