// the built-in look that turns this skin on (Designs → Built-in → Retro 95); palette + stylesheet, so hex is fine here
const CSS = `
html.skin-retro body { font-family: Tahoma, "MS Sans Serif", Verdana, "Bastion Emoji", system-ui, sans-serif; font-size: 13px; }
html body .btn, html body .chip, html body .seg { border-radius: 0; border: 2px solid; border-color: #ffffff #404040 #404040 #ffffff; background: #c0c0c0; color: #000000; box-shadow: inset -1px -1px 0 #808080; }
html body .btn:active, html body .chip.on, html body .seg > button.on { border-color: #404040 #ffffff #ffffff #404040; box-shadow: inset 1px 1px 0 #808080; background: #d4d0c8; color: #000000; }
html body .seg { padding: 0; gap: 0; }
html body .seg > button { border-radius: 0; color: #000000; }
html body .btn.primary { background: #c0c0c0; color: #000000; font-weight: 700; outline: 1px solid #000000; outline-offset: -4px; }
html body .btn.danger { color: #c00000; }
/* inputs: only colours, radius, border width and the --panel-2 fill, never border-style / background / padding, so a page-own borderless field inside its own box (Settings search, the chat bar) stays clean */
html body input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=color]):not([type=file]), html body select, html body textarea { --panel-2: #ffffff; border-radius: 0; border-width: 2px; border-color: #808080 #ffffff #ffffff #808080; color: #000000; }
html body .pill { border-radius: 0; background: #ffffff; border: 1px solid #808080; color: #000000; }
html body .pill.ok { color: #006000; } html body .pill.warn { color: #805000; } html body .pill.bad { color: #c00000; } html body .pill.accent { color: #000080; }
html body .sec { color: #ffffff; text-shadow: 1px 1px 0 #000000; font-weight: 700; }
html body .errbox { border-radius: 0; background: #ffffff; color: #c00000; border: 2px solid #c00000; }
html body .empty-state { color: #404040; }
html body .dcard, html body .topic { border-radius: 0; }
html body ::-webkit-scrollbar-thumb { border-radius: 0; background: #c0c0c0; border: 2px solid; border-color: #ffffff #404040 #404040 #ffffff; }
html body ::-webkit-scrollbar-track { background: #d4d0c8; }
`

export default defineNitroPlugin(() => {
  registerDesignPreset({
    key: 'retro',
    name: 'Retro 95',
    skin: 'retro',
    css: CSS,
    tokens: {
      'bg': '#008080', 'panel': '#c0c0c0', 'panel-2': '#d4d0c8', 'line': '#808080', 'line-2': '#ffffff',
      'text': '#000000', 'muted': '#303030', 'faint': '#505050', 'accent': '#000080', 'ok': '#005a00', 'warn': '#6e4300',
      'bad': '#a00000', 'track': '#a0a0a0', 'claude': '#d97757', 'term-bg': '#000000', 'term-fg': '#c0c0c0', 'radius': 0, 'scheme': 'light',
    },
  })
})
