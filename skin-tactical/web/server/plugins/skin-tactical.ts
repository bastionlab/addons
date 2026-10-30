// the built-in look that turns this skin on (Designs → Built-in → Tactical HUD); palette + stylesheet, so hex is fine here
const CSS = `
:root:root:root body { font-family: "Bahnschrift", "Arial Narrow", "Roboto Condensed", system-ui, sans-serif; }
:root:root:root body .btn, :root:root:root body .chip, :root:root:root body .seg { border-radius: 0; text-transform: uppercase; letter-spacing: .04em; }
:root:root:root body .btn.primary { background: #f2a900; border-color: #f2a900; color: #0d0f0a; clip-path: polygon(6px 0, 100% 0, calc(100% - 6px) 100%, 0 100%); }
:root:root:root body .chip.on, :root:root:root body .seg > button.on { background: #3a3415; color: #f2a900; border-color: #f2a900; }
:root:root:root body .pill { border-radius: 0; text-transform: uppercase; letter-spacing: .04em; }
:root:root:root body input, :root:root:root body select, :root:root:root body textarea { border-radius: 0; background: #0f110b; }
:root:root:root body .sec { color: #f2a900; }
:root:root:root body .errbox { border-radius: 0; border-left: 3px solid #e5483b; }
:root:root:root body ::-webkit-scrollbar-thumb { border-radius: 0; background: #454c36; }
`

export default defineNitroPlugin(() => {
  registerDesignPreset({
    key: 'tactical',
    name: 'Tactical HUD',
    skin: 'tactical',
    css: CSS,
    tokens: {
      'bg': '#0d0f0a', 'panel': '#171a12', 'panel-2': '#20241a', 'line': '#2e3324', 'line-2': '#4a5238',
      'text': '#ebe8d6', 'muted': '#b0ad94', 'faint': '#7c7d65', 'accent': '#f2a900', 'ok': '#8fce4a', 'warn': '#f2a900',
      'bad': '#e5483b', 'track': '#262a1d', 'claude': '#d97757', 'term-bg': '#070806', 'term-fg': '#d6d4c0', 'radius': 2, 'scheme': 'dark',
    },
  })
})
