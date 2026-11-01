<script setup lang="ts">
/**
 * Page greeting, the cute way: the cat's little face peeks in at the top of the page and says a line of its own for
 * this page in a speech bubble (no title: the owner doesn't want a header that only repeats the tab's name). It pops
 * in on every page change; tap the face for another line. Full-screen pages (chat) keep all their height.
 */
const props = withDefaults(defineProps<{ path?: string, title?: string, icon?: string }>(), { path: '/', title: '', icon: '' })
const { t, te } = useI18n()
const FULL = ['/chat']
const show = computed(() => !FULL.includes(props.path))
const seg = computed(() => props.path.split('/')[1] || 'home')
const extra = ref(0)
watch(() => props.path, () => (extra.value = 0))
const line = computed(() => {
  if (extra.value) return t(`skinKawaii.msg.m${extra.value}`)
  const k = `skinKawaii.hi.${seg.value}`
  return te(k) ? t(k) : t('skinKawaii.hi.other')
})
const boop = ref(false)
let bt: ReturnType<typeof setTimeout> | undefined
function poke() {
  let n = extra.value
  while (n === extra.value) n = 1 + Math.floor(Math.random() * 10)
  extra.value = n
  boop.value = false
  nextTick(() => { boop.value = true; clearTimeout(bt); bt = setTimeout(() => (boop.value = false), 600) })
}
onUnmounted(() => clearTimeout(bt))
</script>

<template>
  <div class="kw-frame">
    <Transition name="kw-head" mode="out-in">
      <header v-if="show" :key="path" class="kw-head">
        <button type="button" class="face" :class="{ boop }" :aria-label="$t('skinKawaii.mascot')" @click="poke">
          <svg viewBox="0 0 64 56" width="52" height="46" aria-hidden="true">
            <path d="M12 22 9 4l14 10zM52 22l3-18-14 10z" fill="#fff4e8" stroke="#7a5469" stroke-width="2" stroke-linejoin="round" />
            <path d="M13 17l-1.4-7 6 4zM51 17l1.4-7-6 4z" fill="#ffb8d4" />
            <ellipse cx="32" cy="32" rx="24" ry="19" fill="#fff4e8" stroke="#7a5469" stroke-width="2" />
            <ellipse cx="23" cy="31" rx="2.6" ry="3.2" fill="#4a3043" />
            <ellipse cx="41" cy="31" rx="2.6" ry="3.2" fill="#4a3043" />
            <circle cx="24" cy="30" r=".9" fill="#ffffff" />
            <circle cx="42" cy="30" r=".9" fill="#ffffff" />
            <ellipse cx="17" cy="37" rx="3.6" ry="2.2" fill="#ffadc9" fill-opacity=".85" />
            <ellipse cx="47" cy="37" rx="3.6" ry="2.2" fill="#ffadc9" fill-opacity=".85" />
            <path d="M30.7 35.2h2.6l-1.3 1.5z" fill="#e2668f" />
            <path d="M28.6 37.8c1.1 1.3 2.4 1.3 3.4 0 1 1.3 2.3 1.3 3.4 0" fill="none" stroke="#4a3043" stroke-width="1.3" stroke-linecap="round" />
          </svg>
        </button>
        <div class="txt">
          <Transition name="kw-line" mode="out-in"><p :key="line" class="say" role="status">{{ line }}</p></Transition>
        </div>
      </header>
    </Transition>
    <slot />
  </div>
</template>

<style scoped>
.kw-frame { min-width: 0; }
.kw-head { display: flex; align-items: center; gap: 12px; margin: 2px 0 18px; min-width: 0; }
.face {
  flex: none; display: grid; place-items: center; width: 64px; height: 64px; padding: 0; margin-top: 2px; border-radius: 50%; cursor: pointer;
  background: var(--panel); border: 2px solid color-mix(in srgb, var(--accent) 22%, var(--line));
  box-shadow: 0 4px 0 color-mix(in srgb, var(--accent) 14%, var(--line)), 0 8px 18px rgba(214, 69, 140, .14);
  -webkit-tap-highlight-color: transparent;
}
.face svg { display: block; margin-top: 4px; }
.face:active { transform: translateY(2px); box-shadow: 0 2px 0 color-mix(in srgb, var(--accent) 14%, var(--line)); }
.face.boop svg { animation: kwf-boop .55s cubic-bezier(.34, 1.56, .64, 1); }
.txt { flex: 1; min-width: 0; }
.say {
  position: relative; display: inline-block; max-width: 100%; margin: 0; padding: 7px 13px; border-radius: 16px;
  font-size: 13.5px; font-weight: 800; color: var(--text); background: var(--panel); border: 2px solid var(--line-2);
  box-shadow: 0 3px 0 var(--line);
}
/* the bubble's tail points back at the face */
.say::before { content: ''; position: absolute; left: -9px; top: calc(50% - 7px); border: 7px solid transparent; border-right-color: var(--line-2); border-left: 0; }
.say::after { content: ''; position: absolute; left: -5px; top: calc(50% - 5px); border: 5px solid transparent; border-right-color: var(--panel); border-left: 0; }
.kw-head-enter-active { animation: kwf-pop .45s cubic-bezier(.34, 1.56, .64, 1); }
.kw-head-leave-active { transition: opacity .1s; }
.kw-head-leave-to { opacity: 0; }
.kw-line-enter-active { animation: kwf-pop .35s cubic-bezier(.34, 1.56, .64, 1); transform-origin: left center; }
.kw-line-leave-active { transition: opacity .1s; }
.kw-line-leave-to { opacity: 0; }
@keyframes kwf-pop { 0% { opacity: 0; transform: scale(.85) translateY(6px); } 100% { opacity: 1; transform: none; } }
@keyframes kwf-boop { 0% { transform: none; } 30% { transform: scale(1.15, .85); } 60% { transform: translateY(-5px) scale(.95, 1.06); } 100% { transform: none; } }
@media (max-width: 640px) {
  .kw-head { gap: 10px; margin-bottom: 16px; }
  .face { width: 54px; height: 54px; }
  .face svg { width: 44px; height: 39px; }
  .say { font-size: 13px; padding: 6px 11px; }
}
@media (prefers-reduced-motion: reduce) {
  .kw-head-enter-active, .kw-line-enter-active, .face.boop svg { animation: none; }
}
</style>
