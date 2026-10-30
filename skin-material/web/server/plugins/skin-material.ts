// the built-in look that turns this skin on (Designs → Built-in → Material You): a dark tonal palette from a purple seed
const CSS = `
:root:root:root body ::selection { background: #4f378b; color: #eaddff; }
:root:root:root body ::-webkit-scrollbar-thumb { background: #49454f; border-radius: 8px; }
`

export default defineNitroPlugin(() => {
  registerDesignPreset({
    key: 'material',
    name: 'Material You',
    skin: 'material',
    css: CSS,
    tokens: {
      'bg': '#141218', 'panel': '#211f26', 'panel-2': '#2b2930', 'line': '#49454f', 'line-2': '#938f99',
      'text': '#e6e0e9', 'muted': '#cac4d0', 'faint': '#a29da9', 'accent': '#d0bcff', 'ok': '#8fd9a0', 'warn': '#f0c56c',
      'bad': '#f2b8b5', 'track': '#36343b', 'claude': '#d97757', 'term-bg': '#0f0d13', 'term-fg': '#e6e0e9', 'radius': 24, 'scheme': 'dark',
    },
  })
})
