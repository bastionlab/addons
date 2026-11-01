// the built-in look that turns this skin on (Designs → Built-in → Blocky); palette + stylesheet, so hex is fine here
const CSS = `
:root:root:root body { font-family: "Courier New", Courier, monospace; font-weight: 700; }
:root:root:root body main.wrap { text-shadow: 1px 1px 0 rgba(0,0,0,0.45); }
:root:root:root body main.wrap svg text { text-shadow: none; }
:root:root:root body a { color: #8cf27a; }
:root:root:root body .btn { border-radius: 0; border: 2px solid #000000; background: #7a7a7a; color: #ffffff; font-weight: 700; text-shadow: 2px 2px 0 #3a3a3a; box-shadow: inset 2px 2px 0 #aaaaaa, inset -2px -3px 0 #4a4a4a; transform-origin: 50% 100%; }
:root:root:root body .btn:hover { background: #8b93c9; border-color: #000000; box-shadow: inset 2px 2px 0 #bcc4f5, inset -2px -3px 0 #59609a; }
:root:root:root body .btn:active { animation: skin-blocky-click .16s steps(2); }
:root:root:root body .btn.primary { background: #3f8f2f; box-shadow: inset 2px 2px 0 #79c860, inset -2px -3px 0 #24591a; }
:root:root:root body .btn.danger { background: #a83232; box-shadow: inset 2px 2px 0 #e06a6a, inset -2px -3px 0 #651717; }
:root:root:root body .btn.ghost { background: transparent; border-color: transparent; box-shadow: none; }
:root:root:root body .btn.ghost:hover { background: rgba(255,255,255,0.12); border-color: #000000; }
:root:root:root body .btn:disabled { background: #3c3c3c; color: #a0a0a0; box-shadow: none; }
:root:root:root body .chip { border-radius: 0; border: 2px solid #000000; background: #8b8b8b; color: #ffffff; box-shadow: inset 2px 2px 0 #b5b5b5, inset -2px -2px 0 #555555; }
:root:root:root body .chip.on { background: #3f8f2f; box-shadow: inset 2px 2px 0 #79c860, inset -2px -2px 0 #24591a; }
:root:root:root body .seg { border-radius: 0; border: 2px solid #000000; background: #373737; }
:root:root:root body .seg > button { color: #e0e0e0; border-radius: 0; }
:root:root:root body .seg > button + button { border-left: 2px solid #000000; }
:root:root:root body .seg > button.on { background: #8b8b8b; color: #ffffff; box-shadow: inset 2px 2px 0 #b5b5b5, inset -2px -2px 0 #555555; }
:root:root:root body input, :root:root:root body select, :root:root:root body textarea { border-radius: 0; border: 2px solid #a0a0a0; background: #000000; color: #ffffff; font-family: "Courier New", Courier, monospace; }
:root:root:root body input:focus, :root:root:root body select:focus, :root:root:root body textarea:focus { outline: none; border-color: #ffffff; }
:root:root:root body .pill { border-radius: 0; border: 1px solid #000000; background: #3c3c3c; color: #ffffff; }
:root:root:root body .pill.ok { background: #1f5a16; color: #8cf27a; }
:root:root:root body .pill.warn { background: #5a4a10; color: #ffd23f; }
:root:root:root body .pill.bad { background: #5a1616; color: #ff7a7a; }
:root:root:root body .pill.accent { background: #1f3f5a; color: #8fd2ff; }
:root:root:root body .sec { display: flex; width: fit-content; padding: 4px 10px; text-transform: uppercase; letter-spacing: .04em; color: #ffffff; background: rgba(16,0,16,0.82); border: 2px solid #2a0a5e; box-shadow: inset 0 0 0 1px #5a2aa8; text-shadow: 2px 2px 0 #3a3a3a; }
:root:root:root body .errbox { border-radius: 0; border: 2px solid #000000; background: #5a1616; color: #ffd0d0; }
:root:root:root body ::selection { background: #3f8f2f; color: #ffffff; }
:root:root:root body ::-webkit-scrollbar-thumb { background: #8b8b8b; border-radius: 0; border: 2px solid #000000; }
`

export default defineNitroPlugin(() => {
  registerDesignPreset({
    key: 'blocky',
    name: 'Blocky',
    skin: 'blocky',
    css: CSS,
    tokens: {
      'bg': '#6f9cf0', 'panel': '#6b6b6b', 'panel-2': '#4e4e4e', 'line': '#2b2b2b', 'line-2': '#111111',
      'text': '#ffffff', 'muted': '#e2e2e2', 'faint': '#c9c9c9', 'accent': '#8cf27a', 'ok': '#6dff5a', 'warn': '#ffd23f',
      'bad': '#ff6b6b', 'track': '#3a3a3a', 'claude': '#d97757', 'term-bg': '#000000', 'term-fg': '#e0e0e0', 'radius': 0, 'scheme': 'dark',
    },
  })
})
