// the built-in look that turns this skin on (Designs → Built-in → Disco); palette + stylesheet, so hex is fine here
const CSS = `
:root:root:root body { font-family: "Avenir Next", "Futura", "Trebuchet MS", system-ui, -apple-system, Roboto, sans-serif; }
:root:root:root body a { color: #ff7ad1; }
:root:root:root body .btn { border-radius: 999px; border: 1.5px solid #6b4aa8; background: linear-gradient(180deg, #2e1c52, #1f1238); color: #fbf3ff; font-weight: 700; letter-spacing: .02em; box-shadow: 0 0 0 1px rgba(255,63,180,0.15), 0 4px 14px rgba(255,63,180,0.18); transition: transform .12s, box-shadow .2s, border-color .2s; }
:root:root:root body .btn:hover { border-color: #ff3fb4; box-shadow: 0 0 0 1px rgba(255,63,180,0.4), 0 6px 20px rgba(255,63,180,0.35); }
:root:root:root body .btn:active { transform: scale(0.95); }
:root:root:root body .btn.primary { background: linear-gradient(100deg, #ff3fb4, #b44bff 55%, #3fd8ff); border-color: transparent; color: #ffffff; text-shadow: 0 1px 2px rgba(60,0,60,0.5); }
:root:root:root body .btn.danger { color: #ff8197; border-color: #ff4f6d; }
:root:root:root body .btn.ghost { background: transparent; border-color: transparent; box-shadow: none; }
:root:root:root body .btn.ghost:hover { background: rgba(255,63,180,0.12); }
:root:root:root body .chip { border-radius: 999px; border: 1.5px solid #4a3378; background: #1f1238; color: #e7d8ff; }
:root:root:root body .chip.on { background: linear-gradient(100deg, #ff3fb4, #b44bff); border-color: transparent; color: #ffffff; font-weight: 700; }
:root:root:root body .seg { border-radius: 999px; border: 1.5px solid #4a3378; background: #170c2a; padding: 2px; gap: 2px; }
:root:root:root body .seg > button { border-radius: 999px; color: #d9c6f5; }
:root:root:root body .seg > button + button { border-left: 0; }
:root:root:root body .seg > button.on { background: linear-gradient(100deg, #ff3fb4, #b44bff); color: #ffffff; font-weight: 700; box-shadow: 0 0 12px rgba(255,63,180,0.45); }
:root:root:root body input, :root:root:root body select, :root:root:root body textarea { border-radius: 12px; border: 1.5px solid #4a3378; background: #140a24; color: #fbf3ff; }
:root:root:root body input:focus, :root:root:root body select:focus, :root:root:root body textarea:focus { outline: none; border-color: #ff3fb4; box-shadow: 0 0 0 3px rgba(255,63,180,0.25); }
:root:root:root body .pill { border-radius: 999px; }
:root:root:root body .sec { font-style: italic; font-weight: 800; letter-spacing: .03em; color: #ffe27a; text-shadow: 0 0 10px rgba(255,201,63,0.45); }
:root:root:root body .errbox { border-radius: 14px; border: 1.5px solid #ff4f6d; }
:root:root:root body ::selection { background: #ff3fb4; color: #ffffff; }
:root:root:root body ::-webkit-scrollbar-thumb { background: linear-gradient(#ff3fb4, #3fd8ff); border-radius: 10px; border: 3px solid #0d0618; }
`

export default defineNitroPlugin(() => {
  registerDesignPreset({
    key: 'disco',
    name: 'Disco',
    skin: 'disco',
    css: CSS,
    tokens: {
      'bg': '#0d0618', 'panel': '#1a0f2e', 'panel-2': '#241640', 'line': '#3a2560', 'line-2': '#5a3d8a',
      'text': '#fbf3ff', 'muted': '#d2bdf0', 'faint': '#a08bc0', 'accent': '#ff3fb4', 'ok': '#3ff2a0', 'warn': '#ffc93f',
      'bad': '#ff4f6d', 'track': '#2c1d4a', 'claude': '#d97757', 'term-bg': '#0a0412', 'term-fg': '#f6e9ff', 'radius': 14, 'scheme': 'dark',
    },
  })
})
