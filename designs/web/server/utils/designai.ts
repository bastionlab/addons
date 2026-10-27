import { randomBytes } from 'node:crypto'

/**
 * "Describe a look": Claude (a tool-less `claude -p` on the host, agent /designs/ai/*) turns a few words into a
 * design: name, colour tokens, a stylesheet and optionally one of the installed skins. The answer passes the
 * same cleaners as a hand-made design before it reaches the editor; nothing is saved until the person saves it.
 */
const agentCall = <T = any>(path: string, opts: UpstreamOpts = {}) => {
  const { agentUrl, agentToken } = useRuntimeConfig()
  return upstream<T>('agent', agentUrl, agentToken, path, 30_000, opts)
}

const COLOR_PROPS = Object.fromEntries(COLOR_KEYS.map(k => [k, { type: 'string', pattern: '^#[0-9a-fA-F]{6}$' }]))
export const DESIGN_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['name', 'tokens', 'css', 'skin'],
  properties: {
    name: { type: 'string', maxLength: 40 },
    tokens: {
      type: 'object',
      additionalProperties: false,
      required: [...COLOR_KEYS, 'radius', 'scheme'],
      properties: { ...COLOR_PROPS, radius: { type: 'integer', minimum: 0, maximum: 24 }, scheme: { type: 'string', enum: ['dark', 'light'] } },
    },
    css: { type: 'string' },
    skin: { type: 'string' },
  },
}

const REFERENCE = `
The app: a phone-first home-server dashboard (Nuxt). Every page is built from the same shared pieces, so a stylesheet
can restyle all of them. Content and behaviour must stay the same; only the look changes.

Tokens (CSS custom properties on :root, used by every piece): --bg (page) --panel (cards) --panel-2 (raised:
buttons, inputs, inner boxes) --line (hairlines) --line-2 (borders of controls) --text --muted --faint (three text
levels) --accent (links, primary buttons, active tab) --ok --warn --bad (status) --track (empty part of bars)
--claude (chat brand) --term-bg --term-fg (terminals) --radius (cards) --radius-sm (controls).
*-soft variants (--accent-soft …) are derived from them. scheme = dark|light sets color-scheme.

Hooks you can style (prefix every selector with ":root:root:root body " so it beats the components' scoped styles; for the page background style ":root:root:root body" itself):
- html.skin-<id> (when a skin is on), html[data-page="home|metrics|addons|settings|designs|notes|chat|…"]
- layout: .shell (grid: sidebar + main), aside.side (desktop sidebar: .brand .logo, .find search button, nav a,
  nav a.on = current page, .badge), .tabs (phone bottom tab bar, a / button, .on), .sheet (phone "More" sheet,
  .page tiles), .topbar (phone top bar), main.wrap (the page), .banner
- .sec (section headings), .panel (a card: header > h2 title, .sub, .actions; .panel.folded), .grid .cols-2 .cols-3
- controls: .btn (.primary .ghost .danger .sm .icon), .seg > button(.on) segmented control, .chip(.on) filters,
  .pill (.ok .warn .bad .accent), .dot, .lnk, input, select, textarea, .errbox, .empty-state, kbd
- data: .stat (.lbl label, b value), .topic (Home tile: .hd .ti icon .name .line .chips), .meter, table, .num
- overlays: .toasts, the command palette, the jobs tray
Fonts: only ones a phone/PC already has (system-ui, Georgia, "Courier New", Tahoma, …).

Rules for css: plain CSS only. NO url() (except the uploaded images listed below), image(), @import, @font-face, backslash escapes or <tags> (they are
rejected). Gradients, shadows, borders, transforms, text-transform, letter-spacing, backdrop-filter, animations
(short and subtle, transform/opacity only; never loop filter, box-shadow, blur or background-position: phones lag), pseudo-elements with content are all fine. Keep it readable on a 380px phone, keep touch
targets ≥ 32px, never hide content or controls, keep text contrast high. Up to ~15 kB.
`

export function designPrompt(ask: string, base: any, skins: { skin: string, name: string }[], images: string[] = []) {
  return `You design looks for a web dashboard. Make one design for this request:

"""${ask.slice(0, 1500)}"""

${REFERENCE}
Skins (whole replacement components for nav, cards, stats and home tiles) installed here: ${skins.length ? skins.map(s => `"${s.skin}" (${s.name})`).join(', ') : 'none'}.
Set "skin" to one of those ids only when the request clearly matches it, else "".
${images.length ? `Images the person uploaded for this design (the only url() allowed; use them, e.g. as the page background or a
corner mascot via a fixed ::after on body): ${images.map(u => `url(${u})`).join(', ')}` : ''}

The design it starts from (keep what the request doesn't change):
${JSON.stringify({ name: base?.name, tokens: base?.tokens, css: base?.css ?? '', skin: base?.skin ?? '' })}

Answer with the JSON object only: a short name (≤ 40 chars), every token, the css, the skin.`
}

export async function designAiStart(ask: string, base: any, images: string[] = []) {
  const imgs = images.filter(u => /^\/api\/designs\/img\/[a-f0-9]{24}\.[a-z]+$/.test(u)).slice(0, 8)
  const job = randomBytes(8).toString('hex')
  const skins = PRESETS.filter(p => p.skin).map(p => ({ skin: p.skin!, name: p.name }))
  await agentCall('/designs/ai/start', { method: 'POST', body: { job, prompt: designPrompt(ask, base, skins, imgs), schema: DESIGN_SCHEMA } })
  return { job }
}

export async function designAiJob(job: string) {
  if (!/^[a-f0-9]{16}$/.test(job)) throw createError({ statusCode: 400, statusMessage: 'bad job' })
  const r = await agentCall<any>(`/designs/ai/job?id=${job}`)
  if (r.state !== 'done') return r
  const d = r.result ?? {}
  const c = cleanCss(d.css)
  const skin = cleanSkin(d.skin)
  return {
    state: 'done',
    secs: r.secs,
    design: { name: String(d.name || 'New design').slice(0, 40), tokens: cleanTokens(d.tokens), css: c.css, skin: PRESETS.some(p => p.skin === skin) ? skin : '' },
    warning: c.error ? `The stylesheet was dropped: ${c.error}` : '',
  }
}
