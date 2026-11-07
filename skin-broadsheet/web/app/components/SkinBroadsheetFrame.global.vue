<script setup lang="ts">
/**
 * Each page opens like a newspaper section: a small kicker, a themed headline (not the page name) in heavy display caps between rules,
 * and a fake byline with the edition time. Full-screen pages (/chat) keep all their height: no header.
 */
const props = withDefaults(defineProps<{ path?: string, title?: string, icon?: string }>(), { path: '/', title: '', icon: '' })
const { t } = useI18n()
const FULL = ['/chat']
const isFull = computed(() => FULL.includes(props.path))
const hash = computed(() => {
  let h = 0
  for (const c of props.path) h = (h * 31 + c.charCodeAt(0)) % 997
  return h
})
const kicker = computed(() => t(`skinBroadsheet.kicker${(hash.value % 6) + 1}`))
// a themed headline, never the page's own name
const head = computed(() => (props.path === '/' ? t('skinBroadsheet.frontPage') : t(`skinBroadsheet.headline${((hash.value + 3) % 6) + 1}`)))
const time = ref('')
const stamp = () => (time.value = fmtDate(new Date(), { hour: '2-digit', minute: '2-digit' }))
watch(() => props.path, stamp)
onMounted(stamp)
</script>

<template>
  <div class="bframe">
    <header v-if="!isFull && title" class="sect">
      <p class="kick">{{ kicker }}</p>
      <Transition name="bshead" mode="out-in">
        <h1 :key="head">{{ head }}</h1>
      </Transition>
      <p class="by">
        <span>{{ $t('skinBroadsheet.byline') }}</span>
        <span v-if="time" class="upd">{{ $t('skinBroadsheet.updated', { time }) }}</span>
      </p>
    </header>
    <slot />
  </div>
</template>

<style scoped>
.bframe { min-width: 0; }
.sect { margin: 8px 0 22px; text-align: center; color: var(--text); }
.kick { margin: 0 0 4px; font-style: italic; font-size: 13px; color: var(--accent); letter-spacing: .02em; }
h1 {
  margin: 0; padding: 6px 0 4px; border-top: 1px solid var(--text); border-bottom: 4px solid var(--text);
  font-family: var(--bs-disp); font-weight: 900; font-size: 40px; line-height: 1.05; text-transform: uppercase; letter-spacing: .05em;
}
.by {
  display: flex; justify-content: space-between; gap: 10px; margin: 0; padding: 4px 0; border-bottom: 1px solid var(--line-2);
  font-variant: small-caps; text-transform: lowercase; letter-spacing: .08em; font-size: 13px; color: var(--muted);
}
.upd { font-style: italic; }
.bshead-enter-active { transition: opacity .3s, transform .3s; }
.bshead-leave-active { transition: opacity .1s; }
.bshead-enter-from { opacity: 0; transform: translateY(6px); }
.bshead-leave-to { opacity: 0; }
@media (max-width: 640px) {
  .sect { margin: 10px 0 16px; }
  h1 { font-size: 26px; letter-spacing: .03em; border-bottom-width: 3px; }
  .by { font-size: 12px; }
}
@media (prefers-reduced-motion: reduce) { .bshead-enter-active { transition: none; } }
</style>

<style>
/* page change: a paper page turns (a slight rotate around the spine + fade) */
html.skin-broadsheet .skin-broadsheet-enter-active { transition: opacity .3s ease-out, transform .32s cubic-bezier(.2, .8, .3, 1); transform-origin: 0 40%; }
html.skin-broadsheet .skin-broadsheet-leave-active { transition: opacity .16s ease-in, transform .16s ease-in; transform-origin: 100% 40%; }
html.skin-broadsheet .skin-broadsheet-enter-from { opacity: 0; transform: perspective(1400px) rotateY(-10deg) translateX(14px); }
html.skin-broadsheet .skin-broadsheet-leave-to { opacity: 0; transform: perspective(1400px) rotateY(8deg) translateX(-10px); }
@media (prefers-reduced-motion: reduce) {
  html.skin-broadsheet .skin-broadsheet-enter-active, html.skin-broadsheet .skin-broadsheet-leave-active { transition: opacity .12s; }
  html.skin-broadsheet .skin-broadsheet-enter-from, html.skin-broadsheet .skin-broadsheet-leave-to { transform: none; }
}
</style>
