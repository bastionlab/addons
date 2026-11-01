// the built-in look that turns the Kawaii skin on (Designs → Built-in → Kawaii); palette + stylesheet, so hex is fine here
const CSS = `
:root:root:root body .btn, :root:root:root body .chip, :root:root:root body .seg { border-radius: 999px; border: 2px solid #f3c6da; background: #ffffff; color: #6b4566; font-weight: 700; box-shadow: 0 3px 0 #f3c6da; transition: transform .12s, box-shadow .12s; }
:root:root:root body .btn:active, :root:root:root body .chip:active { transform: translateY(2px); box-shadow: 0 1px 0 #f3c6da; }
:root:root:root body .btn.primary, :root:root:root body .chip.on { background: #ff8fc1; border-color: #e66aa5; color: #4a1238; box-shadow: 0 3px 0 #d0558f; }
:root:root:root body .btn.danger { color: #d6456a; }
:root:root:root body .btn.ghost { background: transparent; box-shadow: none; border-color: transparent; }
:root:root:root body .seg { padding: 2px; gap: 2px; box-shadow: none; }
:root:root:root body .seg > button { border-radius: 999px; }
:root:root:root body .seg > button.on { background: #ffd6e8; color: #b23c78; }
/* inputs: only colours, radius, border width and the --panel-2 fill, never border-style / background / padding, so a page-own borderless field inside its own box (Settings search, the chat bar) stays clean */
:root:root:root body input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=color]):not([type=file]), :root:root:root body select, :root:root:root body textarea { --panel-2: #fffafc; border-width: 2px; border-radius: 14px; border-color: #f3d3e2; color: #5a3d55; }
:root:root:root body input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=color]):not([type=file]):focus, :root:root:root body select:focus, :root:root:root body textarea:focus { outline: none; border-color: #e66aa5; }
:root:root:root body .pill { border-radius: 999px; font-weight: 700; }
:root:root:root body .sec { color: #b23c78; font-weight: 800; letter-spacing: .02em; }
:root:root:root body .sec::before { content: "♡ "; color: #ff8fc1; }
:root:root:root body ::-webkit-scrollbar-thumb { background: #f7bcd6; border-radius: 10px; border: 3px solid transparent; background-clip: padding-box; }
`

export default defineNitroPlugin(() => {
  registerDesignPreset({
    key: 'kawaii',
    name: 'Kawaii',
    skin: 'kawaii',
    css: CSS,
    tokens: {
      'bg': '#fff2f8', 'panel': '#ffffff', 'panel-2': '#fff0f6', 'line': '#f6d7e5', 'line-2': '#eebbd2',
      'text': '#55374f', 'muted': '#85647f', 'faint': '#8a6984', 'accent': '#c8387f', 'ok': '#1f8257', 'warn': '#a5650a',
      'bad': '#cf3358', 'track': '#f8dde9', 'claude': '#d97757', 'term-bg': '#2d2235', 'term-fg': '#f8e8f2', 'radius': 20, 'scheme': 'light',
    },
  })
})
