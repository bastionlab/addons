<script setup lang="ts">
/** each page is a comic page: a yellow halftone caption ("MEANWHILE, IN THE ENGINE ROOM…" on Metrics) slams in on top, a "to be continued" tag closes it */
const props = withDefaults(defineProps<{ path?: string, title?: string, icon?: string }>(), { path: '/', title: '', icon: '' })
const FULL = ['/chat']
const isFull = computed(() => FULL.includes(props.path))
// a themed line per page (never just the tab's name); pages without one get none
const { t, te } = useI18n()
const flavor = computed(() => { const k = `skinComic.places.${props.path.split('/')[1] || 'home'}`; return te(k, 'en') ? t(k) : '' })
</script>

<template>
  <div class="cframe">
    <Transition name="cslam" mode="out-in">
      <div v-if="flavor && !isFull" :key="path" class="caption">
        <span class="txt">{{ flavor }}</span>
      </div>
    </Transition>
    <slot />
    <div v-if="title && !isFull" class="tbc"><span>{{ $t('skinComic.continued') }}</span></div>
  </div>
</template>

<style scoped>
.cframe { min-width: 0; }
.caption {
  position: relative; display: inline-block; max-width: 100%; margin: 4px 0 22px; padding: 10px 18px;
  background: var(--comic-yellow); border: 3px solid var(--line-2); box-shadow: 5px 5px 0 var(--line-2); transform: rotate(-1.2deg);
  overflow: hidden;
}
.caption::after {
  content: ''; position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(circle, rgba(200, 120, 0, .35) 1.3px, rgba(200, 120, 0, 0) 1.8px) 0 0 / 7px 7px;
  -webkit-mask-image: linear-gradient(100deg, rgba(0, 0, 0, 0) 40%, rgba(0, 0, 0, 1));
  mask-image: linear-gradient(100deg, rgba(0, 0, 0, 0) 40%, rgba(0, 0, 0, 1));
}
.txt { position: relative; z-index: 1; font-size: 20px; font-weight: 900; font-style: italic; text-transform: uppercase; letter-spacing: .03em; color: var(--line-2); }
.tbc { display: flex; justify-content: flex-end; margin: 26px 0 0; }
.tbc span { padding: 6px 14px; font-size: 13px; font-weight: 900; font-style: italic; text-transform: uppercase; letter-spacing: .04em; color: var(--line-2); background: var(--comic-yellow); border: 3px solid var(--line-2); box-shadow: 4px 4px 0 var(--line-2); transform: rotate(1.5deg); }
.cslam-enter-active { transition: transform .32s cubic-bezier(.3, 1.6, .5, 1), opacity .12s; }
.cslam-leave-active { transition: opacity .1s; }
.cslam-enter-from { transform: rotate(-8deg) scale(1.35); opacity: 0; }
.cslam-leave-to { opacity: 0; }
@media (max-width: 640px) {
  .caption { margin: 2px 0 16px; padding: 8px 12px; }
  .txt { font-size: 16px; }
}
@media (prefers-reduced-motion: reduce) { .cslam-enter-active { transition: opacity .1s; } .cslam-enter-from { transform: rotate(-1.2deg); } }
</style>

<style>
/* page change: a diagonal panel wipe */
html.skin-comic .skin-comic-enter-active { transition: clip-path .34s cubic-bezier(.6, .05, .3, 1); }
html.skin-comic .skin-comic-leave-active { transition: opacity .12s; }
html.skin-comic .skin-comic-enter-from { clip-path: polygon(0 0, 0 0, -30% 100%, -30% 100%); }
html.skin-comic .skin-comic-enter-to { clip-path: polygon(0 0, 130% 0, 100% 100%, -30% 100%); }
html.skin-comic .skin-comic-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) {
  html.skin-comic .skin-comic-enter-active { transition: opacity .12s; }
  html.skin-comic .skin-comic-enter-from { clip-path: none; opacity: 0; }
  html.skin-comic .skin-comic-enter-to { clip-path: none; }
}
</style>
