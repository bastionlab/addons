// the built-in look that turns this skin on (Designs → Built-in → The Bastion Times); palette + stylesheet, so hex is fine here
const SERIF = '"Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", "Noto Serif", Georgia, "Times New Roman", "Bastion Emoji", serif'
const CSS = `
:root:root:root body { font-family: ${SERIF}; font-size: 15px; }
:root:root:root body h1, :root:root:root body h2, :root:root:root body h3 { font-family: ${SERIF}; letter-spacing: 0; }
:root:root:root body .btn { border-radius: 0; background: transparent; border: 1px solid #1c1813; color: #1c1813; font-family: ${SERIF}; font-variant: small-caps; letter-spacing: .04em; box-shadow: 2px 2px 0 rgba(28,24,19,0.18); }
:root:root:root body .btn:hover { background: #1c1813; color: #f4ecd8; }
:root:root:root body .btn.primary { background: #1c1813; color: #f4ecd8; border-color: #1c1813; }
:root:root:root body .btn.primary:hover { background: #8e1b17; border-color: #8e1b17; }
:root:root:root body .btn.ghost { border-color: transparent; box-shadow: none; }
:root:root:root body .btn.danger { color: #a61c16; border-color: #a61c16; }
:root:root:root body .btn.danger:hover { background: #a61c16; color: #f4ecd8; }
:root:root:root body .chip { border-radius: 0; background: transparent; border: 0; border-bottom: 1px solid #b9aa86; color: #4a4134; font-style: italic; }
:root:root:root body .chip.on { color: #1c1813; border-bottom: 2px solid #1c1813; font-style: normal; font-weight: 700; }
:root:root:root body .seg { border-radius: 0; border-color: #1c1813; }
:root:root:root body .seg > button { border-radius: 0; color: #4a4134; font-variant: small-caps; letter-spacing: .04em; }
:root:root:root body .seg > button.on { background: #1c1813; color: #f4ecd8; }
:root:root:root body .pill { border-radius: 0; background: transparent; border: 1px solid currentColor; font-variant: small-caps; }
:root:root:root body input, :root:root:root body select, :root:root:root body textarea { border-radius: 0; background: #fbf6e9; border: 1px solid #9c8e6c; color: #1c1813; font-family: ${SERIF}; }
:root:root:root body input:focus, :root:root:root body select:focus, :root:root:root body textarea:focus { outline: none; border-color: #1c1813; box-shadow: 0 0 0 1px #1c1813; }
:root:root:root body .sec { font-family: ${SERIF}; font-variant: small-caps; letter-spacing: .08em; font-weight: 700; border-top: 3px double #1c1813; padding-top: 6px; }
:root:root:root body .errbox { border-radius: 0; }
:root:root:root body a { color: #8e1b17; }
:root:root:root body ::selection { background: #1c1813; color: #f4ecd8; }
:root:root:root body ::-webkit-scrollbar-thumb { background: #b9aa86; border-radius: 0; }
`

export default defineNitroPlugin(() => {
  registerDesignPreset({
    key: 'broadsheet',
    name: 'The Bastion Times',
    skin: 'broadsheet',
    css: CSS,
    tokens: {
      'bg': '#f2e9d3', 'panel': '#f6efdd', 'panel-2': '#ebe0c4', 'line': '#d3c5a2', 'line-2': '#9c8e6c',
      'text': '#1c1813', 'muted': '#4a4134', 'faint': '#776b55', 'accent': '#8e1b17', 'ok': '#2d6630', 'warn': '#8f5e00',
      'bad': '#b0201a', 'track': '#e2d5b3', 'claude': '#a85536', 'term-bg': '#1d1a15', 'term-fg': '#efe5cc', 'radius': 0, 'scheme': 'light',
    },
  })
})
