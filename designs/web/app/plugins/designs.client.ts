/** paint this person's design (this kind of device's own, if it has one): the last one at once (no flash of the stock look), then whatever the server says.
 *  Also tags <html> with the page (data-page="home", "metrics", …) so a design's stylesheet can target one page. */
export default defineNuxtPlugin(() => {
  bindSkin(useSkin())
  applyLook(cachedLook(), false)
  $fetch<{ look: Look | null }>(`/api/designs/active?device=${deviceKind()}`).then(r => applyLook(r.look)).catch(() => {})
  const page = (p: string) => (document.documentElement.dataset.page = p.split('/')[1] || 'home')
  page(useRoute().path)
  useRouter().afterEach(to => page(to.path))
  // 'Bastion Emoji': one-colour emoji (Noto Emoji) a skin may put in its font stack so emoji take the text colour
  // (SKINS.md). The browser only fetches it once a skin's stack actually uses it.
  const st = document.createElement('style')
  st.textContent = "@font-face{font-family:'Bastion Emoji';src:url(/fonts/BastionEmoji.woff2) format('woff2');font-display:swap;" +
    'unicode-range:U+A9,U+AE,U+203C,U+2049,U+2122,U+2139,U+2194-21AA,U+231A-23FF,U+24C2,U+25AA-25FE,U+2600-27BF,U+2934-2935,U+2B05-2B55,U+3030,U+303D,U+3297,U+3299,U+1F000-1FAFF,U+FE0F,U+200D,U+20E3}'
  document.head.appendChild(st)
})
