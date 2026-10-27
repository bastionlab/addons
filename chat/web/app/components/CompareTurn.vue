<script setup lang="ts">
import type { Turn } from '~/composables/useAsk'
// one compare turn: the question, then a pane per model, names hidden until the owner picks the best one
const props = defineProps<{ turn: Turn, score: Record<string, number> }>()
const emit = defineEmits<{ vote: [string] }>()
const shown = computed(() => !!props.turn.vote)
const html = (s: string) => {
  const { text, found } = hideSecrets(splitQuestions(s).text)
  return showSecrets(md(text), found)
}
const speed = (tps: number) => `${tps.toFixed(1)} tok/s`
const tab = ref(0) // phones: one pane at a time
</script>

<template>
  <div class="cmp">
    <div class="q">{{ turn.q }}</div>
    <div class="tabs only-phone seg">
      <button v-for="(p, i) in turn.cmp" :key="p.key" type="button" :class="{ on: tab === i }" @click="tab = i">{{ p.key }}<span v-if="p.busy">…</span></button>
    </div>
    <div class="panes">
      <div v-for="(p, i) in turn.cmp" :key="p.key" class="pane" :class="{ won: turn.vote === p.key, hidden: tab !== i }">
        <div class="ph small">
          <b>{{ p.key }}</b>
          <span v-if="shown" class="muted">{{ p.label }}<template v-if="score[p.label]"> · <Icon name="trophy" :size="14"/> {{ score[p.label] }}</template></span>
          <span v-if="p.busy" class="spin" />
          <span v-else-if="shown && p.secs" class="faint">{{ p.secs }} s</span>
          <span v-else-if="shown && p.tps" class="faint">{{ speed(p.tps) }}</span>
        </div>
        <div v-if="p.a" class="a" v-html="html(p.a)" />
        <div v-if="p.error" class="small bad">{{ p.error }}</div>
        <button v-if="!turn.busy && !turn.vote && !p.error" type="button" class="btn sm pickb" @click="emit('vote', p.key)"><Icon name="thumbs-up" :size="16"/> {{ $t('chat.best') }}</button>
      </div>
    </div>
    <div v-if="!turn.busy && !turn.vote" class="small faint">{{ $t('chat.voteHint') }}</div>
  </div>
</template>

<style scoped>
.cmp { display: flex; flex-direction: column; gap: 8px; }
.q { align-self: flex-end; max-width: 85%; background: var(--panel-2); border: 1px solid var(--line); padding: 7px 12px; border-radius: 12px 12px 4px 12px; white-space: pre-wrap; overflow-wrap: anywhere; }
.panes { display: grid; grid-template-columns: repeat(auto-fit, minmax(0, 1fr)); gap: 10px; }
.pane { display: flex; flex-direction: column; gap: 8px; min-width: 0; border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 10px 12px; }
.pane.won { border-color: var(--ok); }
.ph { display: flex; align-items: center; gap: 8px; }
.a { line-height: 1.55; overflow-wrap: anywhere; font-size: 14px; }
.a :deep(p) { margin: 0 0 8px; }
.a :deep(pre) { background: var(--bg); border: 1px solid var(--line); padding: 8px 10px; border-radius: var(--radius-sm); overflow-x: auto; }
.a :deep(code) { font-family: var(--mono); font-size: 12.5px; }
.a :deep(.sec) { filter: blur(5px); }
.pickb { align-self: flex-start; margin-top: auto; }
.spin { width: 12px; height: 12px; border-radius: 50%; border: 2px solid var(--line-2); border-top-color: var(--accent); animation: cspin .8s linear infinite; }
@keyframes cspin { to { transform: rotate(360deg) } }
.tabs { align-self: flex-start; }
@media (max-width: 640px) {
  .panes { grid-template-columns: 1fr; }
  .pane.hidden { display: none; }
}
@media (min-width: 641px) { .tabs { display: none; } }
</style>
