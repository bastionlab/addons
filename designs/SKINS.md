# Writing a skin

A skin is an add-on (`addons/skin-<id>/`, `depends_on: [designs]`, no routes) that changes how the whole
dashboard looks and behaves, while every page keeps its content and function. A design on /designs names the
skin (`skin: <id>`); the person's choice switches it on at runtime, nothing is rebuilt. Reference: `addons/skin-retro`.

## The pieces (all optional)
Global components named `Skin<Pascal id><Piece>.global.vue` in `web/app/components/` (id `tactical` → `SkinTactical…`,
`win11` → `SkinWin11…`). When the skin is on, the core renders yours instead of its own, with the same props/slots:

| Piece | Replaces | Props / slots |
|---|---|---|
| `Nav` | sidebar, phone tab bar, phone top bar, "More" sheet (`layouts/default.vue`) | `nav: {to, icon, label}[]` (pages the viewer may open, in order), `path` (current route), `badge(to) → number` (problems, show it), `mark(to) → '' / 'busy' / 'input'` (chat state dot), `state: 'ok'/'warn'/'bad'` + `stateText` (agent live?), `up` ("7/9 up"), `full` (page fills the screen, e.g. /chat); emits `search` (opens the ⌘K palette). Must work at 380 px (phone) and desktop. Include `<JobsButton />` somewhere (jobs tray). |
| `Backdrop` | nothing; a layer behind everything | `path`. Render `position: fixed; inset: 0; z-index: -1; pointer-events: none`. Also set `html.skin-<id> body { background: transparent; }` (the core paints body opaque, which would hide a z-index -1 layer). Animated art lives here. |
| `Frame` | wraps each page inside `main.wrap` | `path`, `title` (page label, '' when unknown), `icon`; default slot = the page. Page chrome: headers, window frames, mastheads, side art. Always render `<slot />` exactly once. **Never a heading that just repeats the page name** (the owner removed those; the nav already says where you are): either no title, or a themed line per page from your locale keyed by the first path segment (`home`, `metrics`, …, e.g. grimoire's spell names `skinGrimoire.spells.*`, comic's `skinComic.places.*`), none for pages without one. |
| `Panel` | every card (`components/Panel.vue`) | `title`, `sub?`, `id?`, `fold?: 'open'/'closed'/'phone'`; slots `default`, `actions`. Keep folding (tap header) with the same localStorage key: `panel:${id}` or `panel:${route.path}:${title}`. |
| `Stat` | label + value pairs | `label`, `value`, `tone?: ok/warn/bad` |
| `TopicCard` | Home section tiles | `to`, `icon`, `name`, `sub?`, `chips?: {text, tone?}[]`, `more?: {text, sub?, tone?}[]`; must be a `<NuxtLink :to>`, fill its tile (`height: 100%`), clip overflow |
| `PageTabs` | a page's own section tabs (`components/PageTabs.vue`: Settings, Metrics, Media, Money, …) — the in-page bar, never a second sidebar | `tabs: {key, label, icon?, badge?, tone?}[]`, `v-model` (open key; emit `update:modelValue`). One horizontal row: sticky at the top while scrolling (`top: var(--ptabs-top)`), scrolls sideways on a phone with the open tab kept in view, badge visible, tabs ≥ 36 px tall on touch. A skin whose Nav/Frame has a fixed top bar sets `--ptabs-top` on `html.skin-<id>` to that bar's height. |

## Tab bar pins (phone)
The phone bar shows four pinned pages + "more"; which four is the viewer's choice and must be changeable in every
skin that has a bottom bar. Use the core composable, never your own localStorage code:
`const { pinned, isPinned, toggle, editing, full, max } = useNavPins(() => props.nav)` (`pinned` = nav entries in
pin order, `editing` = shared "edit tabs" mode). In the "more" sheet/menu, put an "edit tabs" toggle in your own
style; while `editing`, tapping a page calls `toggle(to)` instead of navigating, pinned pages show a mark, others go
dim once `full`; show "n / max". Leaving the sheet ends editing. Same pins in every look.

## Icons and emoji
Core `<Icon>` draws `svg.icon` (24-grid line icons, `stroke="currentColor"`, width 1.8) everywhere: nav, tabs,
buttons, pages. Restyle them to match your skin in your global style block, e.g.
`html.skin-<id> svg.icon { stroke-width: 2.4; stroke-linecap: square; stroke-linejoin: miter; }`, a glow
(`drop-shadow`, not on phone loops), a tinted fill (`fill: color-mix(in srgb, currentColor 18%, transparent)`).
Keep them legible at 14–18 px. Emoji in page content are colour by default; a skin whose look is monochrome or
ink-on-paper puts the one-colour font in its body stack so emoji take the text colour:
`html.skin-<id> body { font-family: <your font>, 'Bastion Emoji', sans-serif; }` (served by Designs, loaded only
when used). Glyphs you draw yourself (✿, ☘) are fine as they are.

Page changes: `app.vue` uses `<NuxtPage :transition="{ name: 'skin-<id>', mode: 'out-in' }">`, so define
`.skin-<id>-enter-active`, `-leave-active`, `-enter-from`, `-leave-to` in a global style block. Keep them short (≤ 350 ms).

While the skin is on, `<html>` has class `skin-<id>` and `data-page="<first path segment or home>"`.

## The look that turns it on
`web/server/plugins/skin-<id>.ts`:
```ts
export default defineNitroPlugin(() => {
  registerDesignPreset({ key: '<id>', name: 'Shown name', skin: '<id>', css: CSS, tokens: { ...16 colours, radius, scheme } })
})
```
Tokens: `bg panel panel-2 line line-2 text muted faint accent ok warn bad track claude term-bg term-fg` as `#rrggbb`,
`radius` 0–24, `scheme` dark/light. The preset `css` goes through the design filter (no url(), @import, @font-face,
backslashes); prefix selectors with `:root:root:root body ` so they beat scoped component styles. CSS that is part
of the skin itself can instead live in a non-scoped `<style>` block of one of your components, every rule under
`html.skin-<id>` (that block is in the bundle for everyone, so it must not match without the class).

## Rules
- The gate (`python3 addons/.github/check/check.py --id skin-<id> --pr addons`) must pass: no hex colours inside
  `<style>` (use tokens, `rgba()`, `color-mix()`), no native confirm/alert, files < 1 MB. Hex in SVG attributes
  in the template is fine (a warning).
- UI text through `$t('skin<Pascal>.key')` with `web/i18n/locales/en.json` (`scripts/i18n-lint` must not grow).
  Brand-ish decoration strings in mustaches (`{{ 'bastion' }}`) are fine.
- Art is your own: inline SVG, CSS gradients, emoji, canvas. No copied logos, characters or images from games,
  films or anime. "Inspired by" is the point; name things generically.
- Phone first (Samsung Chrome, 380 px): touch targets ≥ 32 px, nothing hover-only, content never hidden,
  keep the page readable (contrast!). Set `--tabbar` on `html.skin-<id> .shell.skinned` to your bottom bar's height
  so pages and the Habits frame leave room, and give `main.wrap` matching padding.
- Motion: transform/opacity only, pause when `document.hidden`, canvases ≤ 30 fps and small, and everything off
  under `@media (prefers-reduced-motion: reduce)`.
- Phone budget (`pointer: coarse` or ≤ 640 px; mid-range Android must stay smooth while scrolling): at most ~3
  continuously running animations, each transform/opacity on its own composited HTML layer (a div with
  `will-change: transform`). Never animate SVG children (`<g>` rotate, rect opacity), box-shadow, filter,
  background-position or clip-path in a loop; no `filter: blur()`/`backdrop-filter` on large or full-screen layers;
  nothing that re-renders a Vue component every frame (keep ticking clocks in tiny child components). Rotate big
  SVG art by rotating a wrapper div, so it is rasterised once. Pointer trails: desktop only; on touch a short burst
  per tap at most.
- Never break the stock look: no global CSS without the `html.skin-<id>` prefix, no core file edits.
- Every save goes live (dash-live rebuilds the app in ~20–40 s; a failed build keeps the old app and says why in
  `/var/lib/dash-live/status.json`). A broken file blocks everyone's build, so keep files compiling.
