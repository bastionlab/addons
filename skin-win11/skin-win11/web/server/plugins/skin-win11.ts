// the built-in look that turns the Windows 11 skin on (Designs → Built-in → Windows 11); palette + stylesheet, so hex is fine here
const CSS = `
:root:root:root body .btn, :root:root:root body .chip { border-radius: 4px; border: 1px solid #3b4357; border-bottom-color: #2a3040; background: #2a3142; color: #f3f5fa; }
:root:root:root body .btn:hover, :root:root:root body .chip:hover { background: #323a4e; }
:root:root:root body .btn:active { background: #262c3b; color: #c8cfdc; }
:root:root:root body .btn.primary, :root:root:root body .chip.on { background: #4cc2ff; border-color: #4cc2ff; border-bottom-color: #3aa8e0; color: #001a29; }
:root:root:root body .btn.primary:hover { background: #62caff; }
:root:root:root body .btn.ghost { background: transparent; border-color: transparent; }
:root:root:root body .btn.ghost:hover { background: #ffffff14; }
:root:root:root body .seg { border-radius: 4px; border-color: #3b4357; background: #232938; }
:root:root:root body .seg > button.on { background: #3a4257; color: #ffffff; box-shadow: inset 0 -2px 0 #4cc2ff; }
/* inputs: only colours, radius, border width and the --panel-2 fill, never border-style / background / padding, so a page-own borderless field inside its own box (Settings search, the chat bar) stays clean */
:root:root:root body input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=color]):not([type=file]), :root:root:root body select, :root:root:root body textarea { --panel-2: #1d2230; border-radius: 4px; border-color: #3b4357; border-bottom-color: #9aa3b5; color: #f3f5fa; }
:root:root:root body input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=color]):not([type=file]):focus, :root:root:root body select:focus, :root:root:root body textarea:focus { outline: none; --panel-2: #161a25; border-bottom-color: #4cc2ff; border-bottom-width: 2px; }
:root:root:root body .pill { border-radius: 4px; }
:root:root:root body .sec { font-weight: 600; letter-spacing: 0; color: #f3f5fa; }
:root:root:root body ::-webkit-scrollbar-thumb { background: #ffffff40; border-radius: 10px; border: 3px solid transparent; background-clip: padding-box; }
`

export default defineNitroPlugin(() => {
  registerDesignPreset({
    key: 'win11',
    name: 'Windows 11',
    skin: 'win11',
    css: CSS,
    tokens: {
      'bg': '#0b1428', 'panel': '#1c2231', 'panel-2': '#252c3d', 'line': '#323a4d', 'line-2': '#465069',
      'text': '#f3f5fa', 'muted': '#b9c1d2', 'faint': '#8993a9', 'accent': '#4cc2ff', 'ok': '#6ccb5f', 'warn': '#fce100',
      'bad': '#ff99a4', 'track': '#343c50', 'claude': '#d97757', 'term-bg': '#0c0c0c', 'term-fg': '#cccccc', 'radius': 8, 'scheme': 'dark',
    },
  })
})
