<script setup lang="ts">
/**
 * Home tile as a tiny terminal: `$ cat ~/media/status`, then the headline, chips as [tags] and detail rows
 * as `> text ...... sub`. Fills its tile and degrades with its container (HomeItem's `tile`).
 */
const props = defineProps<{
  to?: string, icon?: string, name?: string, sub?: string, chips?: { text: string, tone?: string }[]
  more?: { text: string, sub?: string, tone?: string }[]
}>()
const slug = computed(() => (props.to && props.to !== '/' ? props.to.replace(/^\/+/, '') : '~'))
const head = computed(() => props.chips?.[0] ?? (props.sub ? { text: props.sub, tone: '' } : null))
const status = computed(() => {
  const c = props.chips ?? []
  if (c.some(x => x.tone === 'bad')) return 'bad'
  if (c.some(x => x.tone === 'warn')) return 'warn'
  return c.some(x => x.tone) ? 'ok' : ''
})
const tag = computed(() => ({ ok: '[ OK ]', warn: '[WARN]', bad: '[FAIL]' } as Record<string, string>)[status.value] ?? '')
</script>

<template>
  <NuxtLink :to="to ?? '/'" class="topic tcard">
    <span class="top">
      <span class="ps">{{ '$' }}</span>
      <span class="cmd">{{ `cat ~/${slug}` }}</span>
      <span v-if="tag" class="st" :class="status">{{ tag }}</span>
    </span>
    <span class="nm"><Icon :name="icon ?? 'grid'" :size="20" /><span class="nt">{{ name }}</span></span>
    <span v-if="head" class="big" :class="head.tone">{{ head.text }}</span>
    <span v-if="chips && chips.length > 1" class="chips">
      <span v-for="c in chips.slice(1)" :key="c.text" class="cp" :class="c.tone">{{ `[${c.text}]` }}</span>
    </span>
    <span v-if="more?.length" class="more">
      <span v-for="(r, i) in more" :key="i" class="row">
        <span class="rt" :class="r.tone">{{ r.text }}</span><span class="ld" /><span v-if="r.sub" class="rs">{{ r.sub }}</span>
      </span>
    </span>
    <span class="cur" aria-hidden="true" />
  </NuxtLink>
</template>

<style scoped>
.tcard {
  position: relative; display: flex; flex-direction: column; gap: 5px; height: 100%; min-width: 0; overflow: hidden;
  padding: 10px 12px; border: 1px solid var(--line-2); border-radius: 0; background: var(--panel);
  color: var(--text); text-decoration: none; font-family: var(--tm-mono);
  transition: border-color .15s, box-shadow .15s;
}
.tcard:hover { text-decoration: none; border-color: var(--accent); box-shadow: 0 0 16px rgba(57, 255, 106, .18), inset 0 0 20px rgba(57, 255, 106, .05); }
.tcard:active { background: var(--panel-2); }
.top { display: flex; align-items: center; gap: 6px; min-width: 0; font-size: 11.5px; color: var(--faint); }
.ps { color: var(--accent); }
.cmd { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.st { flex: none; font-weight: 700; white-space: pre; color: var(--ok); }
.st.warn { color: var(--warn); } .st.bad { color: var(--bad); }
.nm { display: flex; align-items: center; gap: 8px; min-width: 0; color: var(--accent); font-weight: 700; font-size: 14px; }
.nm .icon { flex: none; }
.nt { min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.big { font-size: 18px; font-weight: 700; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.big.ok { color: var(--ok); } .big.warn { color: var(--warn); } .big.bad { color: var(--bad); }
.chips { display: flex; flex-wrap: wrap; gap: 2px 8px; max-height: 40px; overflow: hidden; font-size: 12px; color: var(--muted); }
.cp.ok { color: var(--ok); } .cp.warn { color: var(--warn); } .cp.bad { color: var(--bad); }
.more { display: none; flex-direction: column; flex: 1; min-height: 0; overflow: hidden; padding-top: 5px; border-top: 1px dashed var(--line); }
.row { display: flex; align-items: baseline; gap: 6px; padding: 1px 0; font-size: 12.5px; min-width: 0; }
.rt { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text); }
.rt::before { content: "> "; color: var(--faint); }
.rt.ok { color: var(--ok); } .rt.warn { color: var(--warn); } .rt.bad { color: var(--bad); }
.ld { flex: 1; min-width: 8px; border-bottom: 1px dotted var(--line-2); transform: translateY(-3px); }
.rs { flex: none; font-size: 11.5px; color: var(--faint); }
.cur { position: absolute; right: 10px; bottom: 9px; width: 8px; height: 14px; background: var(--accent); opacity: 0; }
.tcard:hover .cur, .tcard:focus-visible .cur { opacity: 1; animation: tcblink 1s steps(1) infinite; }
@keyframes tcblink { 50% { opacity: 0; } }

@container tile (max-height: 99px) {
  .tcard { justify-content: center; gap: 3px; padding: 6px 10px; }
  .top, .chips { display: none; }
  .big { font-size: 14px; }
}
@container tile (min-height: 100px) { .more { display: flex; } }
@container tile (min-height: 180px) and (min-width: 240px) { .big { font-size: 22px; } }
@container tile (max-width: 129px) {
  .tcard { align-items: center; justify-content: center; text-align: center; padding: 6px; }
  .top, .chips, .more { display: none; }
  .nm { flex-direction: column; gap: 4px; font-size: 12px; max-width: 100%; }
  .big { font-size: 12px; max-width: 100%; }
}
@media (prefers-reduced-motion: reduce) { .tcard, .cur { transition: none; animation: none !important; } }
</style>
