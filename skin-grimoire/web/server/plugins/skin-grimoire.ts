// the built-in look that turns this skin on (Designs → Built-in → Grimoire): black leather, crimson, gold
const CSS = `
:root:root:root body { background: transparent; }
:root:root:root body ::selection { background: #7a1f2e; color: #f6ead0; }
:root:root:root body ::-webkit-scrollbar-thumb { background: #4a3522; border-radius: 3px; }
:root:root:root body ::-webkit-scrollbar-track { background: #0c0809; }
`

export default defineNitroPlugin(() => {
  registerDesignPreset({
    key: 'grimoire',
    name: 'Grimoire',
    skin: 'grimoire',
    css: CSS,
    tokens: {
      'bg': '#0c0809', 'panel': '#191210', 'panel-2': '#241a16', 'line': '#3b2b20', 'line-2': '#6a4e30',
      'text': '#f0e6cf', 'muted': '#cdb994', 'faint': '#9a8768', 'accent': '#e0405a', 'ok': '#62c46f', 'warn': '#dcae4a',
      'bad': '#ff6b5e', 'track': '#2c201a', 'claude': '#d97757', 'term-bg': '#0a0707', 'term-fg': '#e9dcc0', 'radius': 6, 'scheme': 'dark',
    },
  })
})
