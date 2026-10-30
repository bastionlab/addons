// the built-in look that turns this skin on (Designs → Built-in → Synthwave); palette + stylesheet, so hex is fine here
const CSS = `
:root:root:root body { font-family: "Trebuchet MS", "Futura", "Century Gothic", 'Bastion Emoji', system-ui, sans-serif; }
:root:root:root body .btn { border-color: #6b3a9e; }
:root:root:root body .btn.primary { background: linear-gradient(90deg, #ff4fd8, #8a5cff); border-color: #ff4fd8; color: #10061f; box-shadow: 0 0 12px #ff4fd866; }
:root:root:root body .chip.on, :root:root:root body .seg > button.on { color: #34e6ff; border-color: #34e6ff; box-shadow: 0 0 8px #34e6ff55; text-shadow: 0 0 6px #34e6ff99; }
:root:root:root body .sec { color: #34e6ff; font-style: italic; text-transform: uppercase; letter-spacing: .08em; text-shadow: 0 0 8px #34e6ff88; }
/* inputs: only colours, radius, border width and the --panel-2 fill, never border-style / background / padding, so a page-own borderless field inside its own box (Settings search, the chat bar) stays clean */
:root:root:root body input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=color]):not([type=file]), :root:root:root body select, :root:root:root body textarea { --panel-2: #12082299; border-color: #57307f; }
:root:root:root body input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=color]):not([type=file]):focus-visible, :root:root:root body select:focus-visible, :root:root:root body textarea:focus-visible { border-color: #34e6ff; }
:root:root:root body a { text-shadow: 0 0 6px #ff4fd855; }
:root:root:root body ::-webkit-scrollbar-thumb { background: #57307f; }
`

export default defineNitroPlugin(() => {
  registerDesignPreset({
    key: 'synthwave',
    name: 'Synthwave',
    skin: 'synthwave',
    css: CSS,
    tokens: {
      'bg': '#0b0618', 'panel': '#150b28', 'panel-2': '#1e1036', 'line': '#3a1f5c', 'line-2': '#57307f',
      'text': '#f7ecff', 'muted': '#c9b0e0', 'faint': '#9079ab', 'accent': '#ff4fd8', 'ok': '#3df5c4', 'warn': '#ffcc4d',
      'bad': '#ff5470', 'track': '#24133d', 'claude': '#d97757', 'term-bg': '#07030f', 'term-fg': '#e6d8f5', 'radius': 6, 'scheme': 'dark',
    },
  })
})
