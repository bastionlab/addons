<script setup lang="ts">
/** each page under an 80s title in chrome lettering ("Mainframe" on Metrics — never just the tab's name; none if the page has no title), with a VHS "PLAY ▶" counter (time on this page) top-right */
const props = withDefaults(defineProps<{ path?: string, title?: string, icon?: string }>(), { path: '', title: '', icon: '' })
const FULL = ['/chat']
const full = computed(() => FULL.includes(props.path))
const { t, te } = useI18n()
const flavor = computed(() => { const k = `skinSynthwave.titles.${props.path.split('/')[1] || 'home'}`; return te(k, 'en') ? t(k) : '' })
const start = ref(Date.now())
const now = ref(Date.now())
watch(() => props.path, () => { start.value = Date.now(); now.value = start.value })
let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => (timer = setInterval(() => { if (!document.hidden) now.value = Date.now() }, 1000)))
onUnmounted(() => clearInterval(timer))
const p2 = (n: number) => String(n).padStart(2, '0')
const counter = computed(() => {
  const s = Math.max(0, Math.floor((now.value - start.value) / 1000))
  return `${p2(Math.floor(s / 3600) % 100)}:${p2(Math.floor(s / 60) % 60)}:${p2(s % 60)}`
})
</script>

<template>
  <div class="sw-frame">
    <header v-if="!full" class="mast">
      <h1 v-if="flavor" class="chrome" :data-t="flavor">{{ flavor }}</h1>
      <div class="vhs">
        <span class="play">{{ $t('skinSynthwave.play') }} <b>{{ '▶' }}</b></span>
        <span class="ctr">{{ counter }}</span>
      </div>
    </header>
    <slot />
  </div>
</template>

<style scoped>
.mast { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin: 0 0 18px; min-width: 0; }
.chrome {
  position: relative; margin: 0; min-width: 0; padding: 0 .12em 0 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  font: italic 900 clamp(28px, 6vw, 46px)/1.1 "Futura", "Trebuchet MS", "Arial Black", system-ui, sans-serif; letter-spacing: .02em; text-transform: uppercase;
  background: linear-gradient(180deg, rgb(255 255 255) 0%, rgb(200 230 255) 40%, rgb(60 40 120) 50%, rgb(255 150 230) 54%, rgb(255 236 255) 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  filter: drop-shadow(0 0 6px rgba(255, 79, 216, .75)) drop-shadow(2px 2px 0 rgba(40, 10, 80, .9));
  transform: skewX(-6deg); transform-origin: left bottom;
}
.vhs { flex: none; margin-left: auto; display: flex; flex-direction: column; align-items: flex-end; gap: 2px; padding-top: 4px; font: 700 15px/1.1 ui-monospace, "Courier New", monospace; color: rgb(240 240 255); letter-spacing: .08em; text-shadow: 2px 0 rgba(255, 0, 90, .7), -2px 0 rgba(0, 240, 255, .7); }
.play b { display: inline-block; animation: sw-blink 1s steps(1) infinite; }
.ctr { font-size: 13px; opacity: .9; font-variant-numeric: tabular-nums; }
@keyframes sw-blink { 50% { opacity: 0; } }
@media (max-width: 640px) { .vhs { font-size: 12px; } .ctr { font-size: 11px; } .mast { margin-bottom: 14px; } }
@media (prefers-reduced-motion: reduce) { .play b { animation: none; } }
</style>
