// the built-in look that turns this skin on (Designs → Built-in → Liquid Glass); palette + stylesheet, so hex is fine here
const CSS = `
:root:root:root body { font-family: -apple-system, "SF Pro Display", "SF Pro Text", system-ui, "Segoe UI", Roboto, sans-serif; letter-spacing: -0.005em; }
:root:root:root body .btn { border-radius: 999px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); color: #f2f4fb; box-shadow: inset 0 1px 0 rgba(255,255,255,0.12); backdrop-filter: blur(14px) saturate(160%); -webkit-backdrop-filter: blur(14px) saturate(160%); transition: background .2s, transform .25s cubic-bezier(.34,1.56,.64,1); }
:root:root:root body .btn:hover { background: rgba(255,255,255,0.14); border-color: rgba(255,255,255,0.22); }
:root:root:root body .btn:active { transform: scale(0.96); }
:root:root:root body .btn.primary { background: linear-gradient(180deg, #8fb2ff, #5f84f5); border-color: rgba(255,255,255,0.25); color: #07102a; font-weight: 600; box-shadow: inset 0 1px 0 rgba(255,255,255,0.45), 0 6px 18px rgba(95,132,245,0.35); }
:root:root:root body .btn.ghost { background: transparent; border-color: transparent; box-shadow: none; backdrop-filter: none; -webkit-backdrop-filter: none; }
:root:root:root body .btn.danger { color: #ff8a9b; }
:root:root:root body .chip { border-radius: 999px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); color: #c7cde2; }
:root:root:root body .chip.on { background: rgba(255,255,255,0.9); color: #0b1020; border-color: transparent; font-weight: 600; }
:root:root:root body .seg { border-radius: 999px; padding: 2px; gap: 2px; background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12); }
:root:root:root body .seg > button { border-radius: 999px; border: 0; color: #c7cde2; }
:root:root:root body .seg > button + button { border-left: 0; }
:root:root:root body .seg > button.on { background: rgba(255,255,255,0.9); color: #0b1020; font-weight: 600; box-shadow: 0 2px 8px rgba(0,0,0,0.25); }
/* inputs: only colours, radius, border width and the --panel-2 fill, never border-style / background / padding, so a page-own borderless field inside its own box (Settings search, the chat bar) stays clean */
:root:root:root body input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=color]):not([type=file]), :root:root:root body select, :root:root:root body textarea { --panel-2: rgba(255,255,255,0.06); border-radius: 12px; border-color: rgba(255,255,255,0.16); color: #f2f4fb; }
:root:root:root body input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=color]):not([type=file]):focus, :root:root:root body select:focus, :root:root:root body textarea:focus { outline: none; border-color: rgba(143,178,255,0.75); }
:root:root:root body .pill { border-radius: 999px; background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.1); }
:root:root:root body .sec { font-size: 20px; font-weight: 700; letter-spacing: -0.02em; margin-top: 30px; }
:root:root:root body .errbox { border-radius: 16px; }
:root:root:root body ::selection { background: rgba(122,162,255,0.35); }
:root:root:root body ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.18); border-radius: 10px; border: 3px solid transparent; background-clip: padding-box; }
`

export default defineNitroPlugin(() => {
  registerDesignPreset({
    key: 'glass',
    name: 'Liquid Glass',
    skin: 'glass',
    css: CSS,
    tokens: {
      'bg': '#05060f', 'panel': '#151a2e', 'panel-2': '#1d2340', 'line': '#262d4a', 'line-2': '#363f66',
      'text': '#f2f4fb', 'muted': '#a7aecb', 'faint': '#737b9c', 'accent': '#8fb2ff', 'ok': '#4ade9a', 'warn': '#ffc85a',
      'bad': '#ff6b81', 'track': '#1a2038', 'claude': '#d97757', 'term-bg': '#05060d', 'term-fg': '#dfe3f0', 'radius': 22, 'scheme': 'dark',
    },
  })
})
