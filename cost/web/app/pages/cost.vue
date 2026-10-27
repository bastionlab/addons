<script setup lang="ts">
useHead({ title: 'Cost · pve' })
const { t } = useI18n()
const tab = usePageTab('overview')
const tabs = computed(() => ['overview', 'claude', 'local', 'power'].map(k => ({ key: k, label: t(`cost.tabs.${k}`) })))
const range = ref(30)
const sel = ref<string | null>(null)

// one fetch covers the range and the current month; the old data stays on screen while it refreshes
const sum = ref<CostSummary | null>(null)
const error = ref('')
const busy = ref(false)
async function load() {
  busy.value = true
  try {
    sum.value = await $fetch<CostSummary>('/api/cost/summary', { query: { days: Math.max(range.value, 31) } })
    error.value = ''
  } catch (e: any) { error.value = e?.data?.statusMessage || e?.message || 'error' }
  busy.value = false
}
onMounted(load)
watch(range, () => { sel.value = null; load() })
watch(tab, () => { sel.value = null })

// the last N calendar days ending today; days without records are zero rows, so ranges, totals and "€ per day" use N days
const days = computed<CostDay[]>(() => {
  const have = new Map((sum.value?.days ?? []).map(d => [d.day, d]))
  const out: CostDay[] = []
  const now = new Date()
  for (let i = range.value - 1; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() - i)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    out.push(have.get(key) ?? { day: key, claude: { usd: 0, by_model: {}, turns: 0, learn_usd: 0 }, local: { by_job: {} }, gpu_wh: {}, server_wh: 0 })
  }
  return out
})
const has = computed(() => costHasData(sum.value))
const month = computed(() => sum.value ? costTotals(sum.value, costMonthDays(sum.value)) : null)
const rangeTot = computed(() => sum.value ? costTotals(sum.value, days.value) : null)
const pickedDay = computed(() => days.value.find(d => d.day === sel.value) ?? null)
const dayLabel = (d: string) => fmtDate(d + 'T12:00', { weekday: 'short', day: 'numeric', month: 'short' })
const eurRate = computed(() => sum.value?.settings.usd_eur ?? 0.92)
const kwhRate = computed(() => sum.value?.settings.eur_kwh ?? 0.38)

// --- Claude: stack per model
const models = computed(() => {
  const tot: Record<string, number> = {}
  for (const d of days.value) for (const [m, x] of Object.entries(d.claude?.by_model ?? {})) tot[m] = (tot[m] || 0) + x.usd
  return Object.keys(tot).sort((a, b) => tot[b]! - tot[a]!)
})
const claudeSeries = computed(() => models.value.map((m, i) => ({ key: m, label: costShort(m), color: COST_COLORS[i % COST_COLORS.length]! })))
const claudeBars = computed(() => days.value.map(d => ({ day: d.day, parts: Object.fromEntries(Object.entries(d.claude?.by_model ?? {}).map(([m, x]) => [m, x.usd])) })))

// --- Local AI: stack per job (top 6, rest folded)
const jobs = computed(() => {
  const tot: Record<string, number> = {}
  for (const d of days.value) for (const [j, x] of Object.entries(d.local?.by_job ?? {})) tot[j] = (tot[j] || 0) + x.in + x.out
  return Object.keys(tot).sort((a, b) => tot[b]! - tot[a]!)
})
const shownJobs = computed(() => jobs.value.slice(0, 6))
const hasRest = computed(() => jobs.value.length > 6)
const localSeries = computed(() => [
  ...shownJobs.value.map((j, i) => ({ key: j, label: j, color: COST_COLORS[i]! })),
  ...(hasRest.value ? [{ key: '_rest', label: t('cost.classes.other'), color: COST_COLORS[7]! }] : []),
])
const localBars = computed(() => days.value.map((d) => {
  const parts: Record<string, number> = {}
  for (const [j, x] of Object.entries(d.local?.by_job ?? {})) parts[shownJobs.value.includes(j) ? j : '_rest'] = (parts[shownJobs.value.includes(j) ? j : '_rest'] || 0) + x.in + x.out
  return { day: d.day, parts }
}))
const localDay = computed(() => pickedDay.value ?? days.value.at(-1) ?? null)

// --- Power: GPU kWh per class
const powerSeries = computed(() => GPU_CLASSES.map((c, i) => ({ key: c, label: t(`cost.classes.${c}`), color: COST_COLORS[[0, 2, 1, 7, 4][i]!]! })))
const powerBars = computed(() => days.value.map(d => ({ day: d.day, parts: Object.fromEntries(GPU_CLASSES.map(c => [c, (d.gpu_wh?.[c] || 0) / 1000])) })))
const powerDay = computed(() => pickedDay.value ?? days.value.at(-1) ?? null)
const dayEur = (d: CostDay) => ((costGpuWh(d) + (d.server_wh || 0)) / 1000) * kwhRate.value
const kwhFmt = (n: number) => n.toLocaleString('de-DE', { maximumFractionDigits: n < 1 ? 2 : 1 })
const usdFmt = (n: number) => costUsd(n, n < 10 ? 2 : 0)
</script>

<template>
  <div class="cost">
    <div class="top">
      <h2 class="sec">{{ t('cost.title') }}</h2>
      <div class="seg">
        <button v-for="r in [7, 30, 90]" :key="r" type="button" :class="{ on: range === r }" @click="range = r">{{ t(`cost.range.${r}`) }}</button>
      </div>
    </div>
    <div v-if="error" class="errbox">{{ error }} <button type="button" class="lnk" @click="load">{{ t('cost.retry') }}</button></div>
    <Skeleton v-if="!sum && !error" kind="cards" :n="3" />
    <template v-else-if="sum">
      <p v-if="!sum.proxy?.ok" class="small warnline">{{ t('cost.proxyOff') }}</p>
      <PageTabs v-model="tab" :tabs="tabs" />
      <div v-if="!has" class="empty-state">{{ t('cost.empty') }}</div>

      <template v-else-if="tab === 'overview' && month">
        <Panel :title="t('cost.monthTitle')" :sub="fmtDate(new Date(), { month: 'long', year: 'numeric' })">
          <div class="cards">
            <div class="card"><span class="lbl">{{ t('cost.claudeList') }}</span><b>{{ costUsd(month.usd) }}</b><span class="faint small">{{ fmtMoney(month.eur) }}</span></div>
            <div class="card"><span class="lbl">{{ t('cost.saved') }}</span><b class="ok">{{ costUsd(month.saved) }}</b><span class="faint small">{{ t('cost.savedSub') }}</span></div>
            <div class="card"><span class="lbl">{{ t('cost.localValue') }}</span><b>{{ fmtMoney(month.apiLo) }} – {{ fmtMoney(month.apiHi) }}</b><span class="faint small">{{ t('cost.localValueSub') }}</span></div>
            <div class="card"><span class="lbl">{{ t('cost.electricity') }}</span><b>{{ fmtMoney(month.power) }}</b><span class="faint small">{{ costKwh(month.gpuWh + month.srvWh) }} · {{ t('cost.electricitySub') }}</span></div>
          </div>
          <div class="vs">
            <span class="lbl">{{ t('cost.vsApi') }}</span>
            <span><b>{{ fmtMoney(month.ollamaEur) }}</b> <span class="faint">{{ t('cost.vs') }}</span> <b>{{ t('cost.apiEqRange', { lo: fmtMoney(month.apiLo), hi: fmtMoney(month.apiHi) }) }}</b></span>
            <span class="faint small">{{ t('cost.vsApiSub') }}</span>
          </div>
        </Panel>
        <Panel :title="t('cost.claudeDay')" :sub="t('cost.perDay')">
          <CostBars v-model="sel" :bars="claudeBars" :series="claudeSeries" :fmt="usdFmt" />
          <p class="faint small hint">{{ t('cost.tapBar') }}</p>
        </Panel>
      </template>

      <template v-else-if="tab === 'claude'">
        <Panel :title="t('cost.claudeDay')" :sub="rangeTot ? costUsd(rangeTot.usd) : ''">
          <CostBars v-model="sel" :bars="claudeBars" :series="claudeSeries" :fmt="usdFmt" />
          <p class="faint small hint">{{ t('cost.tapBar') }}</p>
          <div v-if="pickedDay" class="detail">
            <div class="dh"><b>{{ dayLabel(pickedDay.day) }}</b><span class="num">{{ costUsd(pickedDay.claude.usd) }} · {{ fmtMoney(pickedDay.claude.usd * eurRate) }}</span></div>
            <div class="faint small">{{ t('cost.turns', { n: pickedDay.claude.turns }) }}<template v-if="pickedDay.claude.learn_usd"> · {{ t('cost.learn') }} {{ costUsd(pickedDay.claude.learn_usd) }}</template></div>
            <div v-for="(x, m) in pickedDay.claude.by_model" :key="m" class="row">
              <span class="nm">{{ costShort(String(m)) }}</span>
              <span class="faint small tk">{{ costTok(x.in) }} {{ t('cost.in') }} · {{ costTok(x.out) }} {{ t('cost.out') }} · {{ costTok(x.cache_read) }} {{ t('cost.cacheRead') }} · {{ costTok(x.cache_write) }} {{ t('cost.cacheWrite') }}</span>
              <b class="num">{{ costUsd(x.usd) }}</b>
            </div>
          </div>
        </Panel>
        <Panel :title="t('cost.plan')" :sub="t('cost.planSub')">
          <CostPlan :points="sum.plan ?? []" />
        </Panel>
      </template>

      <template v-else-if="tab === 'local'">
        <Panel :title="t('cost.localDay')" :sub="rangeTot ? `${fmtMoney(rangeTot.apiLo)} – ${fmtMoney(rangeTot.apiHi)}` : ''">
          <template v-if="jobs.length">
            <CostBars v-model="sel" :bars="localBars" :series="localSeries" :fmt="costTok" />
            <p class="faint small hint">{{ t('cost.tapBar') }}</p>
            <div v-if="localDay" class="detail">
              <div class="dh">
                <b>{{ dayLabel(localDay.day) }}</b>
                <span class="num">{{ t('cost.apiEq') }} {{ fmtMoney(costLocalApi(sum, localDay)[0] * eurRate) }} – {{ fmtMoney(costLocalApi(sum, localDay)[1] * eurRate) }}</span>
              </div>
              <div v-for="(j, name) in localDay.local.by_job" :key="name" class="row">
                <span class="nm">{{ name }}</span>
                <span class="faint small tk">{{ t('cost.calls', { n: j.calls }) }} · {{ costTok(j.in) }} {{ t('cost.in') }} · {{ costTok(j.out) }} {{ t('cost.out') }}</span>
                <b class="num">{{ costTok(j.in + j.out) }}</b>
              </div>
            </div>
          </template>
          <div v-else class="empty-state">{{ t('cost.noLocal') }}</div>
        </Panel>
      </template>

      <template v-else-if="tab === 'power' && rangeTot">
        <Panel :title="t('cost.powerDay')" :sub="`${costKwh(rangeTot.gpuWh)} · ${t('cost.powerSub')}`">
          <CostBars v-model="sel" :bars="powerBars" :series="powerSeries" :fmt="kwhFmt" />
          <p class="faint small hint">{{ t('cost.tapBar') }}</p>
          <div v-if="powerDay" class="detail">
            <div class="dh"><b>{{ dayLabel(powerDay.day) }}</b><span class="num">{{ fmtMoney(dayEur(powerDay)) }}</span></div>
            <div v-for="c in GPU_CLASSES" :key="c" class="row">
              <span class="nm">{{ t(`cost.classes.${c}`) }}</span><span />
              <b class="num">{{ costKwh(powerDay.gpu_wh?.[c] || 0) }}</b>
            </div>
            <div class="row"><span class="nm">{{ t('cost.server') }}</span><span /><b class="num">{{ costKwh(powerDay.server_wh || 0) }}</b></div>
          </div>
        </Panel>
        <Panel :title="t('cost.electricity')" :sub="t('cost.powerSub')">
          <div class="cards">
            <div class="card"><span class="lbl">{{ t('cost.gpu') }}</span><b>{{ costKwh(rangeTot.gpuWh) }}</b><span class="faint small">{{ fmtMoney((rangeTot.gpuWh / 1000) * kwhRate) }}</span></div>
            <div class="card"><span class="lbl">{{ t('cost.server') }}</span><b>{{ costKwh(rangeTot.srvWh) }}</b><span class="faint small">{{ fmtMoney((rangeTot.srvWh / 1000) * kwhRate) }}</span></div>
            <div class="card"><span class="lbl">{{ t('cost.total') }} · {{ range }} d</span><b>{{ fmtMoney(rangeTot.power) }}</b><span class="faint small">{{ fmtMoney(rangeTot.power / Math.max(days.length, 1)) }} / d</span></div>
            <div class="card"><span class="lbl">{{ t('cost.month') }}</span><b>{{ fmtMoney(month?.power ?? 0) }}</b></div>
          </div>
          <p class="faint small hint">{{ t('cost.serverNote') }}</p>
        </Panel>
      </template>
      <p v-if="sum.proxy?.ok && sum.proxy.since" class="faint small hint">{{ t('cost.proxySince', { d: fmtDate(sum.proxy.since) }) }}</p>
    </template>
  </div>
</template>

<style scoped>
.top { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.top .sec { margin: 0; }
.warnline { color: var(--warn); margin: 8px 0; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; }
.card { background: var(--panel-2); border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 10px; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.card .lbl, .vs .lbl { font-size: 12px; color: var(--faint); }
.card b { font-size: 17px; font-weight: 600; overflow-wrap: anywhere; }
.ok { color: var(--ok); }
.vs { margin-top: 10px; display: flex; flex-direction: column; gap: 2px; }
.hint { margin: 8px 0 0; }
.detail { margin-top: 12px; border-top: 1px solid var(--line); padding-top: 10px; display: flex; flex-direction: column; gap: 6px; }
.dh { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.row { display: grid; grid-template-columns: minmax(70px, auto) 1fr auto; gap: 8px; align-items: baseline; }
.row .tk { min-width: 0; overflow-wrap: anywhere; }
.row .nm { overflow-wrap: anywhere; }
.num { font-variant-numeric: tabular-nums; }
@media (max-width: 640px) { .row { grid-template-columns: 1fr auto; } .row .tk { grid-column: 1 / -1; order: 3; } }
</style>
