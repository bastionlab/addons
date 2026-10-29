<script setup lang="ts">
// slim strip above the chat composer while the hands-free loop runs: state, what it heard, Cancel / Send now / Stop.
// The chat stays visible and usable; nothing covers the screen.
const { state, heard, note, review, stop, interrupt, sendNow, cancel } = useVoiceLoop()
const label = computed(() => $t('voice.' + (state.value === 'off' ? 'listening' : state.value)))
</script>

<template>
  <div class="vdock" role="status" :aria-label="$t('voice.aria')">
    <button type="button" class="dot-btn" :aria-label="$t('voice.hint')" @click="interrupt"><span class="vd" :class="state" /></button>
    <div class="body">
      <div class="small muted">{{ label }}</div>
      <div class="said" :class="{ ghost: !heard && !note }">{{ note || heard || $t('voice.hint') }}</div>
    </div>
    <template v-if="review">
      <button type="button" class="btn sm" @click="cancel">{{ $t('common.cancel') }}</button>
      <button type="button" class="btn sm primary" @click="sendNow">{{ $t('voice.sendNow') }}</button>
    </template>
    <button v-else type="button" class="btn sm ghost" @click="stop"><Icon name="x" :size="14"/> {{ $t('voice.stop') }}</button>
  </div>
</template>

<style scoped>
.vdock { display: flex; align-items: center; gap: 10px; padding: 8px 12px; margin-bottom: 6px; border: 1px solid var(--line); border-radius: var(--radius-sm); background: var(--panel); }
.dot-btn { border: 0; background: none; padding: 6px; min-width: 32px; min-height: 32px; display: grid; place-items: center; cursor: pointer; }
.vd { width: 14px; height: 14px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.vd.listening { animation: vp 1.6s ease-in-out infinite; }
.vd.speaking { animation: vp .9s ease-in-out infinite; }
.vd.waiting, .vd.transcribing, .vd.sending { background: var(--faint); box-shadow: none; animation: vp 2.4s ease-in-out infinite; }
.vd.review { background: var(--warn); box-shadow: none; }
.body { flex: 1; min-width: 0; }
.said { overflow-wrap: anywhere; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.said.ghost { color: var(--faint); }
@keyframes vp { 50% { transform: scale(1.35); } }
@media (prefers-reduced-motion: reduce) { .vd { animation: none !important; } }
</style>
