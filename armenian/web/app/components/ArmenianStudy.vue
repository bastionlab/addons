<script setup lang="ts">
/**
 * The review screen. Recognition cards: Armenian → Show answer → Again / Hard / Good / Easy.
 * Write cards: the English meaning → trace/write it on the pad (Hint shows the glyph, Check scores the ink) or type it (words) → rate.
 * Keys: space = show / Good (the suggested rating), 1–4, z = undo
 */
const props = defineProps<{ start: any }>()
const emit = defineEmits<{ close: [], changed: [] }>()

const q = ref<any>(props.start)
const shown = ref(false)
const busy = ref(false)
const error = ref('')
const savedOffline = ref(false)
const reviewed = ref(0)
const result = ref<{ ok: boolean, typed: string, cov?: number, hint?: boolean, sugg?: number } | null>(null)
const pad = ref<any>()
let t0 = Date.now()
const LABELS = ['Again', 'Hard', 'Good', 'Easy']

const card = computed(() => q.value?.card)
const writing = computed(() => card.value?.kind === 'write')
const word = computed(() => writing.value && card.value.t === 'w')

function take(r: any) {
  q.value = r; shown.value = false; result.value = null; t0 = Date.now(); error.value = ''
}
async function post(body: Record<string, any>) {
  if (busy.value) return
  busy.value = true
  try {
    const r = await $fetch<any>('/api/armenian/action', { method: 'POST', body })
    if (r?.queued) { // offline: the worker keeps the answer and sends it later
      if (body.action === 'undo') { error.value = 'Undo needs a connection'; return }
      take(await $fetch<any>('/api/armenian').then(x => x.next).catch(() => q.value))
      savedOffline.value = true
    } else { take(r); savedOffline.value = false }
    emit('changed'); return true
  }
  catch (e: any) { error.value = e?.data?.statusMessage || e?.message }
  finally { busy.value = false }
}
async function rate(r: number) {
  if (!shown.value || !card.value) return
  if (await post({ action: 'answer', k: card.value.id, rating: r, secs: Math.min(60, (Date.now() - t0) / 1000) })) reviewed.value++
}
async function undo() { if (await post({ action: 'undo' })) reviewed.value = Math.max(0, reviewed.value - 1) }

// --- writing ---
function checked(r: { ok: boolean, typed: string, cov?: number, hint?: boolean, sugg?: number }) { result.value = r; shown.value = true }
/** from the pad's check: pass = Good (Easy if clean from memory), fail = Again, a hint caps it at Good; the learner can change it */
const suggested = computed(() => result.value?.sugg ?? (result.value ? (result.value.ok ? 3 : 1) : 3))
const verdict = computed(() => {
  const r = result.value
  if (!r) return ''
  const pct = r.cov === undefined ? '' : ` · ${Math.round(r.cov * 100)}%`
  return (r.typed.trim() ? (r.ok ? 'Correct' : 'Not quite') : (r.ok ? 'Nice' : 'Try again')) + pct
})
/** per character: does it match the answer at the same place (positional diff, enough for short words) */
const diff = computed(() => {
  const r = result.value
  if (!r || r.ok) return []
  const a = [...answerOf(card.value).normalize('NFC').toLowerCase()]
  return [...r.typed.normalize('NFC').toLowerCase()].map((ch, i) => ({ ch, bad: ch !== a[i] }))
})

// which counter the card on screen comes out of (underlined, like Anki)
const from = computed(() => { const s = card.value?.state; return s === 'new' ? 'new' : s === 'review' ? 'review' : s ? 'learn' : '' })

// waiting for a learning step: count down, then ask again
const left = ref(0)
let tick: any
watch(() => q.value?.wait, (w) => {
  clearInterval(tick)
  left.value = w || 0
  if (!w || q.value?.card) return
  tick = setInterval(async () => {
    if (--left.value > 0) return
    clearInterval(tick)
    take(await $fetch<any>('/api/armenian').then(r => r.next).catch(() => q.value))
  }, 1000)
}, { immediate: true })
onUnmounted(() => clearInterval(tick))
const mmss = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`

function onKey(e: KeyboardEvent) {
  if (e.target instanceof HTMLInputElement || e.ctrlKey || e.metaKey || e.altKey) return
  if (e.key === 'Escape') emit('close')
  else if (e.key === ' ' || e.key === 'Enter') {
    e.preventDefault()
    if (shown.value) rate(suggested.value)
    else if (!writing.value) shown.value = true
  }
  else if (/^[1-4]$/.test(e.key)) rate(Number(e.key))
  else if (e.key === 'z') undo()
}
onMounted(() => { window.addEventListener('keydown', onKey); document.documentElement.style.overflow = 'hidden' })
onUnmounted(() => { window.removeEventListener('keydown', onKey); document.documentElement.style.overflow = '' })
</script>

<template>
  <div class="study">
    <header>
      <button type="button" class="btn ghost icon" aria-label="close" @click="emit('close')"><Icon name="x" :size="16"/></button>
      <div class="counts">
        <span class="c-new" :class="{ on: from === 'new' }">{{ q.new }}</span>
        <span class="c-learn" :class="{ on: from === 'learn' }">{{ q.learn }}</span>
        <span class="c-rev" :class="{ on: from === 'review' }">{{ q.review }}</span>
      </div>
      <button type="button" class="btn ghost sm" :disabled="busy || !reviewed" @click="undo">Undo</button>
    </header>

    <p v-if="error" class="errbox">{{ error }}</p>
    <p v-if="savedOffline" class="small"><span class="pill warn">Saved offline, syncs when online</span></p>

    <!-- write card: the meaning, then the learner produces the Armenian -->
    <main v-if="card && writing" :key="card.id + card.reps">
      <div class="meta">
        <span class="pill">{{ groupName(card.g) }}</span>
        <span class="pill accent">{{ word ? 'write the word' : 'write the letter' }}</span>
        <span v-if="card.state === 'new'" class="pill accent">new</span>
      </div>
      <div class="prompt">
        <div class="mean">{{ card.en.join(', ') }}</div>
        <div v-if="card.t === 'l'" class="muted">{{ card.tr }}</div>
      </div>
      <ArmenianWrite ref="pad" :c="card" :locked="shown" @check="checked" />
      <template v-if="shown">
        <div v-if="result" class="verdict" :class="result.ok ? 'ok' : 'bad'">{{ verdict }}</div>
        <div v-if="diff.length" lang="hy" class="typedd"><span v-for="(d, i) in diff" :key="i" :class="{ bad: d.bad }">{{ d.ch }}</span></div>
        <div lang="hy" class="glyph sm">{{ card.hy }}</div>
        <ArmenianFace :c="card" />
      </template>
    </main>

    <!-- recognition card -->
    <main v-else-if="card" :key="card.id + card.reps" @click="shown = true">
      <div class="meta"><span class="pill">{{ groupName(card.g) }}</span><span v-if="card.state === 'new'" class="pill accent">new</span><span v-if="card.lapses >= 4" class="pill warn">leech</span></div>
      <div lang="hy" class="glyph" :class="{ sm: card.t === 'w' }">{{ card.hy }}</div>
      <ArmenianFace v-if="shown" :c="card" />
    </main>

    <main v-else class="done">
      <template v-if="q.wait">
        <div class="big"><Icon name="clock" :size="40"/></div>
        <b>Next learning card in {{ mmss(left) }}</b>
      </template>
      <template v-else>
        <div class="big"><Icon name="circle-check" :size="40"/></div>
        <b>Done for today</b>
        <span class="muted small">{{ reviewed }} reviewed this session</span>
      </template>
      <button type="button" class="btn" @click="emit('close')">Close</button>
    </main>

    <footer v-if="card">
      <div v-if="!shown && writing" class="two">
        <button type="button" class="btn" :class="{ on: pad?.showHint }" @click="pad?.toggleHint()"><Icon name="eye" :size="16"/>Hint</button>
        <button type="button" class="btn" @click="shown = true">I don't know</button>
        <button type="button" class="btn primary" :disabled="!pad?.canCheck" @click="pad?.check()">Check</button>
      </div>
      <button v-else-if="!shown" type="button" class="btn primary show" @click="shown = true">Show answer</button>
      <div v-else class="rate">
        <button v-for="(l, i) in LABELS" :key="l" type="button" class="btn" :class="[`r${i + 1}`, { sugg: writing && result && suggested === i + 1 }]" :disabled="busy" @click="rate(i + 1)">
          <span class="ivl">{{ q.buttons?.[i] }}</span>{{ l }}
        </button>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.study { position: fixed; inset: 0; z-index: 60; background: var(--bg); display: flex; flex-direction: column; padding: env(safe-area-inset-top) 0 env(safe-area-inset-bottom); }
header { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-bottom: 1px solid var(--line); max-width: 760px; width: 100%; margin: 0 auto; }
.counts { flex: 1; display: flex; justify-content: center; gap: 16px; font-weight: 650; font-size: 16px; }
.counts span { padding: 0 2px 1px; border-bottom: 2px solid transparent; }
.counts .on { border-bottom-color: currentColor; }
.c-new { color: var(--accent); } .c-learn { color: var(--bad); } .c-rev { color: var(--ok); }
.errbox { margin: 10px auto 0; max-width: 720px; }
main { flex: 1; overflow-y: auto; padding: 18px 16px 24px; display: flex; flex-direction: column; gap: 14px; max-width: 640px; width: 100%; margin: 0 auto; }
.meta { display: flex; gap: 6px; justify-content: center; flex-wrap: wrap; }
.glyph { font-size: 112px; line-height: 1.15; text-align: center; font-weight: 400; user-select: none; overflow-wrap: anywhere; }
.glyph.sm { font-size: 56px; }
.spk { align-self: center; min-width: 44px; min-height: 44px; }
.prompt { text-align: center; display: flex; flex-direction: column; gap: 2px; }
.prompt .mean { font-size: 22px; font-weight: 600; }
.verdict { text-align: center; font-weight: 600; }
.verdict.ok { color: var(--ok); } .verdict.bad { color: var(--bad); }
.typedd { text-align: center; font-size: 26px; }
.typedd .bad { color: var(--bad); text-decoration: underline; }
.done { align-items: center; justify-content: center; text-align: center; gap: 8px; }
.big { font-size: 48px; }
footer { border-top: 1px solid var(--line); padding: 10px 14px calc(10px + env(safe-area-inset-bottom)); max-width: 760px; width: 100%; margin: 0 auto; }
.show { width: 100%; min-height: 48px; font-size: 15px; }
.two { display: grid; grid-template-columns: 1fr 1.4fr 1fr; gap: 8px; }
.two .btn.on { border-color: var(--accent); color: var(--accent); }
.two .btn { min-height: 48px; }
.rate { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.rate .btn { flex-direction: column; gap: 0; min-height: 52px; font-size: 13.5px; font-weight: 600; }
.rate .sugg { border-color: currentColor; box-shadow: 0 0 0 1px currentColor inset; }
.ivl { font-size: 11px; font-weight: 400; color: var(--muted); }
.r1 { color: var(--bad); } .r2 { color: var(--warn); } .r3 { color: var(--ok); } .r4 { color: var(--accent); }
@media (max-width: 640px) { .glyph { font-size: 96px; } .glyph.sm { font-size: 48px; } main { padding: 12px 12px 18px; gap: 10px; } }
</style>
