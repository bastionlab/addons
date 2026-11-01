// the built-in look that turns this skin on (Designs → Built-in → Hacker Terminal); palette + stylesheet, so hex is fine here
const MONO = '"JetBrains Mono", "Fira Code", "Cascadia Code", "Ubuntu Mono", "DejaVu Sans Mono", "Droid Sans Mono", Menlo, Consolas, "Bastion Emoji", monospace'
const CSS = `
:root:root:root body { font-family: ${MONO}; text-shadow: 0 0 3px rgba(57,255,106,0.28); }
:root:root:root body h1, :root:root:root body h2, :root:root:root body h3 { font-family: ${MONO}; letter-spacing: 0; }
:root:root:root body .btn { border-radius: 0; background: transparent; border: 1px solid #1f6b3a; color: #9dffb0; font-family: ${MONO}; }
:root:root:root body .btn:hover { background: #39ff6a; color: #021006; border-color: #39ff6a; text-shadow: none; }
:root:root:root body .btn.primary { background: #39ff6a; border-color: #39ff6a; color: #021006; font-weight: 700; text-shadow: none; box-shadow: 0 0 12px rgba(57,255,106,0.35); }
:root:root:root body .btn.primary:hover { background: #9dffb0; }
:root:root:root body .btn.ghost { border-color: transparent; }
:root:root:root body .btn.danger { color: #ff5c5c; border-color: #6b1f1f; }
:root:root:root body .btn.danger:hover { background: #ff5c5c; color: #160303; }
:root:root:root body .chip { border-radius: 0; background: transparent; border: 1px dashed #1f6b3a; color: #6fd88a; }
:root:root:root body .chip.on { background: #39ff6a; color: #021006; border: 1px solid #39ff6a; text-shadow: none; }
:root:root:root body .seg { border-radius: 0; border-color: #1f6b3a; }
:root:root:root body .seg > button { border-radius: 0; color: #6fd88a; }
:root:root:root body .seg > button.on { background: #39ff6a; color: #021006; text-shadow: none; }
:root:root:root body .pill { border-radius: 0; background: transparent; border: 1px solid currentColor; }
:root:root:root body input, :root:root:root body select, :root:root:root body textarea { border-radius: 0; background: #020a04; border: 1px solid #1f6b3a; color: #c8ffd4; font-family: ${MONO}; caret-color: #39ff6a; }
:root:root:root body input:focus, :root:root:root body select:focus, :root:root:root body textarea:focus { outline: none; border-color: #39ff6a; box-shadow: 0 0 0 1px #39ff6a, 0 0 14px rgba(57,255,106,0.25); }
:root:root:root body .sec { font-family: ${MONO}; text-transform: lowercase; letter-spacing: 0; color: #39ff6a; }
:root:root:root body .sec::before { content: "## "; color: #3a8a52; }
:root:root:root body .errbox { border-radius: 0; border-style: dashed; }
:root:root:root body ::selection { background: #39ff6a; color: #021006; text-shadow: none; }
:root:root:root body ::-webkit-scrollbar-thumb { background: #1f6b3a; border-radius: 0; }
`

export default defineNitroPlugin(() => {
  registerDesignPreset({
    key: 'terminal',
    name: 'Hacker Terminal',
    skin: 'terminal',
    css: CSS,
    tokens: {
      'bg': '#020804', 'panel': '#04100a', 'panel-2': '#08190f', 'line': '#123a20', 'line-2': '#1f6b3a',
      'text': '#c8ffd4', 'muted': '#6fd88a', 'faint': '#3f8f57', 'accent': '#39ff6a', 'ok': '#39ff6a', 'warn': '#ffcc33',
      'bad': '#ff5c5c', 'track': '#0b2414', 'claude': '#d97757', 'term-bg': '#010402', 'term-fg': '#9dffb0', 'radius': 0, 'scheme': 'dark',
    },
  })
})
