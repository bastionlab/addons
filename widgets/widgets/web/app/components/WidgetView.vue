<script setup lang="ts">
import { asList, asSeries, fmtNum, type WidgetDef } from '../utils/widgets'

/** one widget, live: polls /api/widgets/data (the server validates and reads the source); a button asks twice before it fires */
const props = defineProps<{ def: WidgetDef, packs?: string[], preview?: boolean }>()
const { t } = useI18n()
const { toast } = useToast()
const val = ref<any>(null)
const label = ref('')
const err = ref('')
const ready = ref(false)
const hist = ref<number[]>([])
const busy = ref(false)
let seq = 0

async function load() {
  if (props.def.look === 'button' || props.def.look === 'component') { ready.value = true; return }
  const mine = ++seq
  try {
    const r = await $fetch<{ value: any, label?: string }>('/api/widgets/data', { method: 'POST', body: { def: props.def } })
    if (mine !== seq) return
    val.value = r.value; label.value = r.label ?? ''; err.value = ''
    if (props.def.look === 'sparkline' && !Array.isArray(r.value) && Number.isFinite(Number(r.value))) hist.value = [...hist.value, Number(r.value)].slice(-40)
  } catch (e: any) { if (mine === seq) err.value = e?.data?.statusMessage || e?.statusMessage || e?.message || 'failed' }
  ready.value = true
}
usePoll(load, 30_000)
watch(() => JSON.stringify(props.def), () => { val.value = null; hist.value = []; ready.value = false; load() })

const d = computed(() => props.def)
const num = computed(() => fmtNum(val.value, d.value.format))
const lines = computed(() => asList(val.value, d.value.format))
const series = computed(() => (Array.isArray(val.value) ? asSeries(val.value, d.value.format) : hist.value))
const pts = computed(() => {
  const s = series.value
  if (s.length < 2) return ''
  const lo = Math.min(...s), hi = Math.max(...s), span = hi - lo || 1
  return s.map((v, i) => `${(i / (s.length - 1) * 100).toFixed(1)},${(30 - (v - lo) / span * 28 - 1).toFixed(1)}`).join(' ')
})
const frac = computed(() => Math.min(1, Math.max(0, Number(val.value) / (d.value.format?.max || 100))) || 0)
const tone = computed(() => (val.value === 'Down' ? 'bad' : val.value === 'Up' ? 'ok' : ''))
const isComp = computed(() => d.value.look === 'component' && !!d.value.pack && (props.packs ?? []).includes(d.value.pack))

const { armed, arm } = useArm()
async function press() {
  if (props.preview) return
  if (!arm(d.value.id)) return // first tap asks "Sure?", the second runs it
  busy.value = true
  try { await $fetch('/api/widgets/press', { method: 'POST', body: { def: d.value } }); toast(t('widgets.pressed', { name: d.value.name })) }
  catch (e: any) { toast(e?.data?.statusMessage || t('widgets.pressFailed')) }
  busy.value = false
}
</script>

<template>
  <div class="w" :class="[`sz-${def.size}`, def.look]">
    <div class="nm">{{ def.name }}<span v-if="label && def.look !== 'text'" class="faint"> · {{ label }}</span></div>
    <template v-if="def.look === 'button' && def.button">
      <button type="button" class="btn" :class="{ danger: armed === def.id }" :disabled="busy" @click="press">{{ armed === def.id ? $t('widgets.sure') : def.button.label }}</button>
    </template>
    <component :is="resolveComponent(def.component!)" v-else-if="isComp" :def="def" />
    <div v-else-if="def.look === 'component'" class="muted small">{{ $t('widgets.packMissing') }}</div>
    <div v-else-if="err" class="bad small">{{ err }}</div>
    <Skeleton v-else-if="!ready" kind="lines" />
    <template v-else>
      <div v-if="def.look === 'number'" class="big num" :class="tone">{{ num }}</div>
      <template v-else-if="def.look === 'sparkline'">
        <div class="big num">{{ series.length ? fmtNum(series[series.length - 1], def.format) : '–' }}</div>
        <svg v-if="pts" viewBox="0 0 100 30" preserveAspectRatio="none" class="spark"><polyline :points="pts" fill="none" stroke="currentColor" stroke-width="1.5" vector-effect="non-scaling-stroke" /></svg>
        <div v-else class="muted small">{{ $t('widgets.collecting') }}</div>
      </template>
      <template v-else-if="def.look === 'gauge'">
        <div class="big num">{{ num }}</div>
        <div class="bar"><i :style="{ width: `${frac * 100}%` }" /></div>
      </template>
      <ul v-else-if="def.look === 'list'" class="ls">
        <li v-for="(l, i) in lines" :key="i">{{ l }}</li>
        <li v-if="!lines.length" class="muted">{{ $t('widgets.nothing') }}</li>
      </ul>
      <div v-else class="txt">{{ typeof val === 'string' ? val : JSON.stringify(val) }}</div>
    </template>
  </div>
</template>

<style scoped>
.w { height: 100%; min-height: 0; display: flex; flex-direction: column; gap: 6px; padding: 12px; background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); overflow: hidden; }
.nm { font-size: 12px; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.big { font-size: 26px; font-weight: 600; line-height: 1.1; }
.big.ok { color: var(--ok); }
.big.bad { color: var(--bad); }
.spark { width: 100%; flex: 1; min-height: 28px; color: var(--accent); }
.bar { height: 8px; border-radius: 4px; background: var(--track); overflow: hidden; }
.bar i { display: block; height: 100%; background: var(--accent); }
.ls { margin: 0; padding: 0; list-style: none; font-size: 13px; overflow: auto; min-height: 0; }
.ls li { padding: 2px 0; border-bottom: 1px solid var(--line); }
.ls li:last-child { border: 0; }
.txt { font-size: 13px; white-space: pre-wrap; overflow: auto; min-height: 0; overflow-wrap: anywhere; }
.w.button { justify-content: center; }
@media (pointer: coarse) { .w .btn { min-height: 36px; } }
</style>
