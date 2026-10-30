// the built-in look that turns this skin on (Designs → Built-in → Comic Book); palette + stylesheet, so hex is fine here
const CSS = `
:root:root:root body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
:root:root:root body a { color: #1e5bd8; font-weight: 600; }
:root:root:root body .btn { border: 2.5px solid #111111; border-radius: 8px; background: #ffffff; color: #111111; font-weight: 800; text-transform: uppercase; letter-spacing: .02em; box-shadow: 3px 3px 0 #111111; transition: transform .08s, box-shadow .08s; }
:root:root:root body .btn:hover { background: #fff6cf; border-color: #111111; }
:root:root:root body .btn:active { transform: translate(2px, 2px); box-shadow: 1px 1px 0 #111111; }
:root:root:root body .btn.primary { background: #ffd83d; color: #111111; }
:root:root:root body .btn.danger { background: #e3262f; color: #ffffff; }
:root:root:root body .btn.ghost { background: transparent; border-color: transparent; box-shadow: none; }
:root:root:root body .btn.ghost:hover { background: #fff1c9; border-color: #111111; }
:root:root:root body .chip { border: 2px solid #111111; background: #ffffff; color: #111111; font-weight: 700; }
:root:root:root body .chip.on { background: #1e5bd8; color: #ffffff; border-color: #111111; }
:root:root:root body .seg { border: 2.5px solid #111111; border-radius: 8px; box-shadow: 3px 3px 0 #111111; background: #ffffff; }
:root:root:root body .seg > button { color: #111111; font-weight: 700; }
:root:root:root body .seg > button + button { border-left: 2px solid #111111; }
:root:root:root body .seg > button.on { background: #ffd83d; color: #111111; }
/* inputs: only colours, radius, border width and the --panel-2 fill, never border-style / background / padding, so a page-own borderless field inside its own box (Settings search, the chat bar) stays clean */
:root:root:root body input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=color]):not([type=file]), :root:root:root body select, :root:root:root body textarea { --panel-2: #ffffff; border-width: 2.5px; border-color: #111111; border-radius: 6px; color: #111111; }
:root:root:root body input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=color]):not([type=file]):focus, :root:root:root body select:focus, :root:root:root body textarea:focus { outline: none; border-color: #1e5bd8; }
:root:root:root body .pill { border: 1.5px solid #111111; font-weight: 700; background: #ffffff; color: #111111; }
:root:root:root body .pill.ok { background: #c9f2d2; color: #0c5a1f; border-color: #111111; }
:root:root:root body .pill.warn { background: #ffe39a; color: #6b3b00; border-color: #111111; }
:root:root:root body .pill.bad { background: #ffc9cc; color: #9b0010; border-color: #111111; }
:root:root:root body .pill.accent { background: #cfe0ff; color: #12398f; border-color: #111111; }
:root:root:root body .sec { text-transform: uppercase; font-weight: 900; font-style: italic; letter-spacing: .02em; border-bottom: 3px solid #111111; padding-bottom: 4px; }
:root:root:root body .errbox { border: 2.5px solid #111111; background: #ffe0e0; color: #9b0010; border-radius: 6px; box-shadow: 3px 3px 0 #111111; }
:root:root:root body ::selection { background: #ffd83d; color: #111111; }
:root:root:root body ::-webkit-scrollbar-thumb { background: #111111; border-radius: 0; border: 3px solid #fff8e7; }
`

export default defineNitroPlugin(() => {
  registerDesignPreset({
    key: 'comic',
    name: 'Comic Book',
    skin: 'comic',
    css: CSS,
    tokens: {
      'bg': '#fff8e7', 'panel': '#ffffff', 'panel-2': '#fff1c9', 'line': '#1a1a1a', 'line-2': '#111111',
      'text': '#141414', 'muted': '#3b3b3b', 'faint': '#666666', 'accent': '#1e5bd8', 'ok': '#157a2e', 'warn': '#a65a00',
      'bad': '#d81f2a', 'track': '#f0e2b8', 'claude': '#d97757', 'term-bg': '#141414', 'term-fg': '#fff8e7', 'radius': 6, 'scheme': 'light',
    },
  })
})
