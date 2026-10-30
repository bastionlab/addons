<script setup lang="ts">
/**
 * Each page opens under a disco marquee: the page title in glittering gold on a dark board, framed by a ring of
 * light bulbs that chase round it (three interleaved bulb sets lit in turn), with a few twinkling sparkles and a
 * sheen sweeping across the letters. On desktop it hangs just under the mirror ball.
 */
const props = withDefaults(defineProps<{ path?: string, title?: string, icon?: string }>(), { path: '/', title: '', icon: '' })
const FULL = ['/chat']
const isFull = computed(() => FULL.includes(props.path))
const SPARKS = [{ l: '6%', t: '18%', d: '0s' }, { l: '38%', t: '-6%', d: '.7s' }, { l: '71%', t: '22%', d: '1.4s' }, { l: '94%', t: '-2%', d: '2.1s' }, { l: '55%', t: '78%', d: '1s' }]
</script>

<template>
  <div class="dframe" :class="{ full: isFull }">
    <Transition name="dmq" mode="out-in" appear>
      <div v-if="title && !isFull" :key="path" class="mq">
        <i class="bulbs k1" aria-hidden="true" /><i class="bulbs k2" aria-hidden="true" /><i class="bulbs k3" aria-hidden="true" />
        <div class="board">
          <small class="sub">{{ $t('skinDisco.tonight') }}</small>
          <h1 class="ttl">
            <Icon v-if="icon" :name="icon" :size="22" class="ti" />
            <span class="tt">{{ title }}</span>
            <i v-for="(s, i) in SPARKS" :key="i" class="spk" :style="{ left: s.l, top: s.t, animationDelay: s.d }" aria-hidden="true">✦</i>
          </h1>
        </div>
      </div>
    </Transition>
    <slot />
  </div>
</template>

<style scoped>
.dframe { min-width: 0; }
.mq {
  position: relative; display: block; width: fit-content; max-width: 100%; margin: 76px auto 24px; padding: 14px;
  border-radius: 18px; background: linear-gradient(180deg, rgba(120, 28, 70, 1), rgba(70, 14, 50, 1));
  box-shadow: 0 0 0 2px rgba(255, 201, 63, .7), 0 0 34px rgba(255, 63, 180, .35), 0 12px 30px rgba(0, 0, 0, .5);
}
.bulbs {
  position: absolute; inset: 0; border-radius: 18px; padding: 12px; pointer-events: none;
  background: radial-gradient(circle, rgba(255, 250, 220, 1) 0 2.4px, rgba(255, 201, 63, .75) 3.4px, rgba(255, 201, 63, 0) 6px) -2px -2px / 18px 18px;
  -webkit-mask: linear-gradient(rgba(0, 0, 0, 1) 0 0) content-box, linear-gradient(rgba(0, 0, 0, 1) 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude;
  animation: chase .75s steps(1) infinite;
}
.k2 { background-position: 4px 4px; animation-delay: .25s; }
.k3 { background-position: 10px 10px; animation-delay: .5s; }
@keyframes chase { 0% { opacity: 1; } 33.3% { opacity: .12; } }
.board {
  position: relative; padding: 10px 26px 12px; border-radius: 10px; text-align: center;
  background: radial-gradient(120% 140% at 50% 0%, rgba(40, 16, 66, 1), rgba(10, 4, 20, 1));
  box-shadow: inset 0 0 18px rgba(0, 0, 0, .8);
}
.sub { display: block; font-size: 10px; font-weight: 800; letter-spacing: .26em; text-transform: uppercase; color: var(--accent); text-shadow: 0 0 8px rgba(255, 63, 180, .8); }
.ttl { position: relative; margin: 2px 0 0; display: inline-flex; align-items: center; gap: 10px; max-width: 100%; overflow: hidden; padding: 0 4px; }
.ti { flex: none; color: var(--warn); filter: drop-shadow(0 0 6px rgba(255, 201, 63, .8)); }
.tt {
  min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  font-size: 30px; font-weight: 900; font-style: italic; letter-spacing: .03em; line-height: 1.2;
  color: var(--warn);
  background: linear-gradient(180deg, rgba(255, 252, 230, 1) 0%, rgba(255, 214, 90, 1) 45%, rgba(214, 140, 20, 1) 55%, rgba(255, 236, 150, 1) 100%);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 0 8px rgba(255, 180, 60, .55));
}
.ttl::after {
  content: ''; position: absolute; top: 0; bottom: 0; left: 0; width: 40%; pointer-events: none;
  background: linear-gradient(100deg, rgba(255, 255, 255, 0), rgba(255, 255, 255, .55), rgba(255, 255, 255, 0));
  mix-blend-mode: overlay; transform: translateX(-120%) skewX(-18deg); animation: sheen 4.5s ease-in-out 1s infinite;
}
@keyframes sheen { 0%, 60% { transform: translateX(-120%) skewX(-18deg); } 100% { transform: translateX(320%) skewX(-18deg); } }
.spk { position: absolute; font-size: 11px; font-style: normal; color: var(--text); text-shadow: 0 0 6px rgba(255, 255, 255, .9); animation: twinkle 2.8s ease-in-out infinite; opacity: 0; pointer-events: none; }
@keyframes twinkle { 0%, 100% { opacity: 0; transform: scale(.3) rotate(0); } 50% { opacity: 1; transform: scale(1) rotate(90deg); } }
.dmq-enter-active { transition: transform .4s cubic-bezier(.3, 1.6, .5, 1), opacity .2s; }
.dmq-leave-active { transition: opacity .1s; }
.dmq-enter-from { transform: translateY(-24px) scale(.85); opacity: 0; }
.dmq-leave-to { opacity: 0; }
@media (max-width: 640px) {
  .mq { margin: 6px auto 18px; padding: 11px; }
  .bulbs { padding: 10px; background-size: 15px 15px; }
  .board { padding: 7px 14px 9px; }
  .tt { font-size: 22px; }
  .sub { font-size: 9px; letter-spacing: .2em; }
}
@media (prefers-reduced-motion: reduce) {
  .bulbs, .ttl::after, .spk { animation: none; }
  .k2, .k3 { opacity: .35; }
  .spk { opacity: .7; }
  .dmq-enter-active { transition: opacity .1s; }
  .dmq-enter-from { transform: none; }
}
</style>

<style>
/* page change: a quick spin-in */
html.skin-disco .skin-disco-enter-active { transition: transform .3s cubic-bezier(.3, 1.4, .5, 1), opacity .22s; transform-origin: 50% 0; }
html.skin-disco .skin-disco-leave-active { transition: opacity .12s; }
html.skin-disco .skin-disco-enter-from { transform: rotate(3deg) scale(.94); opacity: 0; }
html.skin-disco .skin-disco-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) {
  html.skin-disco .skin-disco-enter-active { transition: opacity .12s; }
  html.skin-disco .skin-disco-enter-from { transform: none; }
}
</style>
