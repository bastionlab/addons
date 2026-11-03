<script setup lang="ts">
// ranking + head to head of models by four headline indexes (llm-stats.com benchmarks), with the fit and speed on this box
const { t } = useI18n()
const data = ref<any>(null)
const error = ref('')
const mode = ref<'rank' | 'duel'>('rank')
// which chart sits above the content: radar belongs to head to head, bars and scatter to the ranking
const view = ref<'table' | 'radar' | 'bars' | 'scatter'>('table')
function setView(v: 'table' | 'radar' | 'bars' | 'scatter') {
  view.value = v
  if (v === 'radar') mode.value = 'duel'
  else if (v !== 'table') mode.value = 'rank'
}
function setMode(m: 'rank' | 'duel') {
  mode.value = m
  if ((view.value === 'radar') !== (m === 'duel')) view.value = 'table'
}
const filter = ref<'installed' | 'fits' | 'open' | 'all'>('fits')
const q = ref('')
const sort = ref({ key: 'score', dir: -1 })
const limit = ref(120)
const picks = ref<string[]>([])
const pickQ = ref('')

async function load() {
  try {
    data.value = await $fetch<any>('/api/ai/compare')
    error.value = ''
  } catch (e: any) { error.value = e?.data?.statusMessage || e?.message || 'error' }
}
onMounted(load)

const rows = computed<any[]>(() => data.value?.rows ?? [])
const byId = computed(() => new Map(rows.value.map(r => [r.id, r])))
// rank = place by Score among all models that have one
const rankOf = computed(() => {
  const m = new Map<string, number>()
  rows.value.filter(r => r.score != null).sort((a, b) => b.score - a.score).forEach((r, i) => m.set(r.id, i + 1))
  return m
})
const tone = (v: string) => (v === 'fits' ? 'ok' : v === 'partial' ? 'warn' : v === 'no' ? 'bad' : '')

const IDX = ['reasoning', 'coding', 'knowledge', 'agents']
const val = (r: any, k: string) => (k === 'name' ? r.name.toLowerCase() : k === 'arena' ? r.arena?.elo : IDX.includes(k) ? r.indexes?.[k]?.v : r[k])
const list = computed(() => {
  const s = q.value.trim().toLowerCase()
  let out = rows.value.filter(r => {
    if (filter.value === 'installed' && !r.installed) return false
    if (filter.value === 'fits' && !['fits', 'partial'].includes(r.fit)) return false
    if (filter.value === 'open' && !r.open) return false
    return !s || `${r.name} ${r.org} ${r.id}`.toLowerCase().includes(s)
  })
  const { key, dir } = sort.value
  out = [...out].sort((a, b) => {
    const x = val(a, key), y = val(b, key)
    if (x == null && y == null) return 0
    if (x == null) return 1
    if (y == null) return -1
    return (x < y ? -1 : x > y ? 1 : 0) * dir
  })
  // models without a Score stay listed below the scored ones, installed first
  const has = (r: any) => (key === 'arena' ? r.arena != null : r.score != null)
  const scored = out.filter(has)
  const rest = out.filter(r => !has(r))
  return [...scored, ...rest.filter(r => r.installed), ...rest.filter(r => !r.installed)]
})
watch([filter, q, sort], () => { limit.value = 120 }, { deep: true })
function sortBy(key: string) {
  sort.value = sort.value.key === key ? { key, dir: -sort.value.dir } : { key, dir: key === 'name' ? 1 : -1 }
}
const arrow = (k: string) => (sort.value.key === k ? (sort.value.dir < 0 ? 'desc' : 'asc') : '')

function toggle(id: string) {
  if (picks.value.includes(id)) picks.value = picks.value.filter(p => p !== id)
  else if (picks.value.length < 3) picks.value = [...picks.value, id]
}
const chosen = computed(() => picks.value.map(id => byId.value.get(id)).filter(Boolean) as any[])
// combobox: every model, installed first, then Score, then name; typing only filters
const norm = (x: string) => x.toLowerCase().replace(/[-._\s]+/g, '')
const CAP = 150
const pickOpen = ref(false)
const active = ref(0)
const root = ref<HTMLElement | null>(null)
const pickList = ref<HTMLElement | null>(null)
const sorted = computed(() => [...rows.value].sort((a, b) =>
  (+!!b.installed - +!!a.installed) || ((b.score ?? -1) - (a.score ?? -1)) || a.name.localeCompare(b.name)))
const matches = computed(() => {
  const s = norm(pickQ.value)
  return s ? sorted.value.filter(r => norm(`${r.name} ${r.id} ${r.org}`).includes(s)) : sorted.value
})
const shown = computed(() => matches.value.slice(0, CAP))
watch(pickQ, () => { active.value = 0; pickOpen.value = true })
function add(id: string) {
  if (picks.value.includes(id) || picks.value.length >= 3) return
  picks.value = [...picks.value, id]
  pickQ.value = ''
  pickOpen.value = false
}
function scrollActive() {
  nextTick(() => pickList.value?.querySelector<HTMLElement>(`[data-i="${active.value}"]`)?.scrollIntoView({ block: 'nearest' }))
}
function pickKey(e: KeyboardEvent) {
  const n = shown.value.length
  if (e.key === 'Escape') { pickOpen.value = false; return }
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    e.preventDefault()
    pickOpen.value = true
    if (n) active.value = (active.value + (e.key === 'ArrowDown' ? 1 : n - 1)) % n
    scrollActive()
  } else if (e.key === 'Enter' && pickOpen.value && shown.value[active.value]) {
    e.preventDefault()
    add(shown.value[active.value].id)
  }
}
function outside(e: Event) { if (root.value && !root.value.contains(e.target as Node)) pickOpen.value = false }
onMounted(() => document.addEventListener('pointerdown', outside))
onBeforeUnmount(() => document.removeEventListener('pointerdown', outside))

// best value per ranking column, among the rows currently listed
const colBest = computed(() => {
  const m: Record<string, number> = {}
  const get: Record<string, (r: any) => number | null> = { score: r => r.score, arena: r => r.arena?.elo, reasoning: r => r.indexes?.reasoning?.v, coding: r => r.indexes?.coding?.v, agents: r => r.indexes?.agents?.v }
  for (const k in get) m[k] = Math.max(-1, ...list.value.map(get[k]).filter(v => v != null) as number[])
  return m
})
const isBest = (k: string, v: number | null) => v != null && v >= 0 && v === colBest.value[k]
const best = (vals: (number | null)[], v: number | null, low = false) => {
  const ok = vals.filter(x => x != null) as number[]
  return v != null && ok.length > 1 && v === (low ? Math.min(...ok) : Math.max(...ok))
}
// head to head compares only the benchmarks every picked model has: per index the mean over those shared keys
// (null when none), Score = mean of the indexes that have one. Pure, so the ranking table can keep its own averages.
function sharedStats(models: any[], groups: Record<string, string[]>) {
  const keys: string[] = []
  const idx: Record<string, ({ v: number; n: number } | null)[]> = {}
  for (const g in groups) {
    const ks = groups[g].filter(k => models.length > 1 && models.every(m => m.bench?.[k] != null))
    keys.push(...ks)
    idx[g] = models.map(m => (ks.length ? { v: ks.reduce((n, k) => n + m.bench[k], 0) / ks.length, n: ks.length } : null))
  }
  const score = models.map((_, i) => {
    const v = Object.values(idx).map(a => a[i]).filter(x => x != null) as { v: number }[]
    return v.length ? v.reduce((n, x) => n + x.v, 0) / v.length : null
  })
  return { keys, idx, score }
}
const GROUPS = computed<Record<string, string[]>>(() => data.value?.groups ?? {})
const shared = computed(() => sharedStats(chosen.value, GROUPS.value))
// the picked models with their shared-benchmark indexes in place of the all-benchmark ones (radar)
const chosenShared = computed(() => chosen.value.map((r, i) => ({ ...r, indexes: Object.fromEntries(IDX.map(k => [k, shared.value.idx[k]?.[i] ?? null])) })))
const idxVals = (k: string) => (shared.value.idx[k] ?? []).map(x => x?.v ?? null)
// wins = indexes where a model is ahead (needs at least two models with a value)
const winN = computed(() => {
  const cmp = IDX.filter(k => idxVals(k).filter(v => v != null).length > 1)
  return { of: cmp.length, n: chosen.value.map((_, i) => cmp.filter(k => best(idxVals(k), idxVals(k)[i])).length) }
})
const verdict = computed(() => {
  const sc = shared.value.score.map(v => (v == null ? null : Math.round(v * 100)))
  const top = Math.max(-1, ...sc.map(v => v ?? -1))
  return sc.filter(v => v != null).length > 1 && sc.filter(v => v === top).length === 1 ? chosen.value[sc.indexOf(top)].name : ''
})
const sharedNote = computed(() => {
  const n = shared.value.keys.length
  if (!n) return t('ai.cmp.noCommon')
  return n <= 4 ? t('ai.cmp.sharedList', { n, list: shared.value.keys.map(k => t(`ai.cmp.bench.${k}`)).join(', ') }, n) : t('ai.cmp.shared', { n }, n)
})
const glance = computed(() => {
  const rows: any[] = [{ k: 'score', label: t('ai.cmp.score'), raw: shared.value.score, txt: (_: any, i: number) => (shared.value.score[i] != null ? pct(shared.value.score[i]) : '') }]
  if (chosen.value.some(r => r.arena)) rows.push({ k: 'arena', label: t('ai.cmp.arena'), raw: chosen.value.map(r => r.arena?.elo ?? null), txt: (r: any) => (r.arena ? String(r.arena.elo) : ''), sub: (r: any) => (r.arena?.rank ? t('ai.cmp.arenaRank', { n: r.arena.rank }) : '') })
  for (const k of ['reasoning', 'coding', 'agents']) {
    rows.push({ k, label: t(`ai.cmp.idx.${k}`), raw: idxVals(k), txt: (_: any, i: number) => (shared.value.idx[k]?.[i] ? pct(shared.value.idx[k][i]!.v) : ''), sub: (_: any, i: number) => (shared.value.idx[k]?.[i] ? t('ai.cmp.evals', { n: shared.value.idx[k][i]!.n }) : '') })
  }
  rows.push({ k: 'wins', label: t('ai.cmp.winsRow'), raw: winN.value.n, txt: (_: any, i: number) => (winN.value.of ? `${winN.value.n[i]} of ${winN.value.of}` : '') })
  rows.push({ k: 'pin', label: t('ai.cmp.priceIn'), raw: chosen.value.map(r => r.price_in), low: true, txt: (r: any) => (r.price_in != null ? `$${r.price_in}` : '') })
  rows.push({ k: 'pout', label: t('ai.cmp.priceOut'), raw: chosen.value.map(r => r.price_out), low: true, txt: (r: any) => (r.price_out != null ? `$${r.price_out}` : '') })
  rows.push({ k: 'ctx', label: t('ai.cmp.context'), raw: chosen.value.map(r => r.context), txt: (r: any) => (r.context != null ? ctxFmt(r.context) : '') })
  return rows
})
const hw = computed(() => chosen.value.some(r => r.installed && r.tokens_per_s != null))
const pct = (v: number | null) => `${Math.round((v ?? 0) * 100)}%`
const fewEv = (r: any, k: string) => r.indexes?.[k]?.n === 1
const ctxFmt = (n: number | null) => (n == null ? t('ai.cmp.na') : n >= 1e6 ? `${+(n / 1e6).toFixed(1)}M` : `${Math.round(n / 1024)}k`)
const parms = (r: any) => (r.params_b == null ? t('ai.cmp.na') : `${r.params_b}B${r.is_moe ? ' MoE' : ''}`)
const ms = (n: number | null) => (n == null ? t('ai.cmp.na') : n >= 1000 ? `${(n / 1000).toFixed(1)} s` : `${n} ms`)
const fitTxt = (v: string) => t(`ai.verdict.${v}`)
const srcLine = computed(() => (data.value?.sources ?? []).map((x: any) => (x.at ? `${x.name} ${fmtDate(x.at * 1000)}` : x.name)).join('; '))
</script>

<template>
  <Panel :title="$t('ai.cmp.title')">
    <div v-if="error" class="errbox">{{ error }}</div>
    <div v-if="!data && !error" class="sk-wrap">
      <Skeleton kind="band" />
      <Skeleton kind="rows" :n="8" />
    </div>
    <template v-if="data">
      <div class="bar">
        <div class="seg">
          <button :class="{ on: mode === 'rank' }" @click="setMode('rank')">{{ $t('ai.cmp.ranking') }}</button>
          <button :class="{ on: mode === 'duel' }" @click="setMode('duel')">{{ $t('ai.cmp.duel') }}<template v-if="chosen.length"> ({{ chosen.length }})</template></button>
        </div>
        <div class="seg">
          <button v-for="v in ['table', 'radar', 'bars', 'scatter']" :key="v" :class="{ on: view === v }" @click="setView(v as any)">{{ $t(`ai.cmp.view.${v}`) }}</button>
        </div>
      </div>

      <template v-if="mode === 'rank'">
        <div class="bar scroll-x nowrap">
          <button v-for="f in ['installed', 'fits', 'open', 'all']" :key="f" class="chip" :class="{ on: filter === f }" @click="filter = f as any">{{ $t(`ai.cmp.filter.${f}`) }}</button>
        </div>
        <input v-model="q" type="search" class="search" :placeholder="$t('ai.cmp.search')">
        <div v-if="view === 'bars' || view === 'scatter'" class="chartbox">
          <AiRankBars v-if="view === 'bars'" :rows="list" :picks="picks" @select="toggle" />
          <AiScatter v-else :rows="list" :picks="picks" />
        </div>
        <div v-if="list.length" class="scroll-x tbl">
          <table class="cmp">
            <thead>
              <tr>
                <th class="stick"><button class="lnk sortb" @click="sortBy('name')">{{ $t('ai.model') }}<Icon v-if="arrow('name')" :name="arrow('name') === 'desc' ? 'chevron-down' : 'chevron-up'" :size="12" /></button></th>
                <th class="num sc"><button class="lnk sortb" @click="sortBy('score')">{{ $t('ai.cmp.score') }}<Icon v-if="arrow('score')" :name="arrow('score') === 'desc' ? 'chevron-down' : 'chevron-up'" :size="12" /></button></th>
                <th class="num"><button class="lnk sortb" @click="sortBy('arena')">{{ $t('ai.cmp.arena') }}<Icon v-if="arrow('arena')" :name="arrow('arena') === 'desc' ? 'chevron-down' : 'chevron-up'" :size="12" /></button></th>
                <th v-for="k in ['reasoning', 'coding', 'agents']" :key="k" class="num"><button class="lnk sortb" @click="sortBy(k)">{{ $t(`ai.cmp.idx.${k}`) }}<Icon v-if="arrow(k)" :name="arrow(k) === 'desc' ? 'chevron-down' : 'chevron-up'" :size="12" /></button></th>
                <th>{{ $t('ai.cmp.fit') }}</th>
                <th>{{ $t('ai.installed') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in list.slice(0, limit)" :key="r.id" class="row" :class="{ sel: picks.includes(r.id), unscored: r.score == null }" @click="toggle(r.id)">
                <td class="stick">
                  <div class="who">
                    <span class="rk faint small">{{ rankOf.get(r.id) ?? '-' }}</span>
                    <div class="who-t">
                      <div class="nm">{{ r.name }}<Icon v-if="picks.includes(r.id)" name="check" :size="14" class="tick" /></div>
                      <div class="muted small">{{ r.org }}<template v-if="r.params_b != null">, {{ parms(r) }}</template></div>
                    </div>
                  </div>
                </td>
                <td class="num sc">
                  <template v-if="r.score != null">
                    <span class="sv" :class="{ best: isBest('score', r.score) }">{{ pct(r.score) }}</span>
                    <div class="mini"><div class="mini-f" :style="{ width: pct(r.score) }" /></div>
                  </template>
                  <span v-else class="muted small">{{ $t('ai.cmp.notScored') }}</span>
                </td>
                <td class="num">
                  <template v-if="r.arena">
                    <span :class="{ best: isBest('arena', r.arena.elo) }">{{ r.arena.elo }}</span>
                    <div v-if="r.arena.rank" class="faint small">{{ $t('ai.cmp.arenaRank', { n: r.arena.rank }) }}</div>
                  </template>
                  <span v-else class="faint">{{ $t('ai.cmp.na') }}</span>
                </td>
                <td v-for="k in ['reasoning', 'coding', 'agents']" :key="k" class="num">
                  <template v-if="r.indexes?.[k]">
                    <span :class="{ best: isBest(k, r.indexes[k].v) }">{{ pct(r.indexes[k].v) }}</span>
                    <div v-if="fewEv(r, k)" class="faint small">{{ $t('ai.cmp.evals', { n: 1 }) }}</div>
                  </template>
                  <span v-else class="faint">{{ $t('ai.cmp.na') }}</span>
                </td>
                <td><span class="pill" :class="tone(r.fit) === 'bad' ? '' : tone(r.fit)">{{ fitTxt(r.fit) }}</span></td>
                <td><span v-if="r.installed" class="pill accent">{{ $t('ai.installed') }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="empty-state">{{ $t('ai.empty') }}</p>
        <div v-if="list.length > limit" class="more"><button class="btn" @click="limit += 120">{{ $t('ai.cmp.more', { n: list.length - limit }) }}</button></div>
      </template>

      <template v-else>
        <div v-if="chosen.length < 3" ref="root" class="combo">
          <div class="combo-in">
            <Icon name="search" :size="16" class="combo-ic" />
            <input v-model="pickQ" type="text" class="search" role="combobox" :aria-expanded="pickOpen" autocomplete="off" autocapitalize="off" spellcheck="false" :placeholder="$t('ai.cmp.pick')" @focus="pickOpen = true" @click="pickOpen = true" @keydown="pickKey">
          </div>
          <div v-if="pickOpen" ref="pickList" class="pop" role="listbox">
            <div v-if="!shown.length" class="pop-note">{{ $t('ai.cmp.noMatch') }}</div>
            <button v-for="(r, i) in shown" :key="r.id" type="button" role="option" class="pop-row" :data-i="i" :class="{ act: i === active, picked: picks.includes(r.id) }" :disabled="picks.includes(r.id)" :aria-selected="picks.includes(r.id)" @click="add(r.id)" @mousemove="active = i">
              <span class="pop-t">
                <span class="nm">{{ r.name }}</span>
                <span class="muted small">{{ r.org }}<template v-if="r.params_b != null">, {{ parms(r) }}</template></span>
              </span>
              <span class="pop-p">
                <span class="pill" :class="tone(r.fit) === 'bad' ? '' : tone(r.fit)">{{ fitTxt(r.fit) }}</span>
                <span v-if="r.installed" class="pill accent">{{ $t('ai.installed') }}</span>
                <Icon v-if="picks.includes(r.id)" name="check" :size="14" class="tick" />
              </span>
            </button>
            <div v-if="matches.length > CAP" class="pop-note">{{ $t('ai.cmp.narrow', { n: matches.length - CAP }) }}</div>
          </div>
        </div>

        <div v-if="view === 'radar' && chosen.length >= 2" class="chartbox"><AiRadar :models="chosenShared" /></div>
        <div v-if="chosen.length" class="heads" :style="{ '--n': chosen.length }">
          <div v-for="r in chosen" :key="r.id" class="hcard">
            <button class="btn ghost icon sm rm" :aria-label="$t('ai.cmp.remove', { name: r.name })" @click="toggle(r.id)"><Icon name="x" :size="14" /></button>
            <div class="nm">{{ r.name }}</div>
            <div class="muted small">{{ r.org }}</div>
            <div class="pills">
              <span class="pill" :class="tone(r.fit) === 'bad' ? '' : tone(r.fit)">{{ fitTxt(r.fit) }}</span>
              <span v-if="r.installed" class="pill accent">{{ $t('ai.installed') }}</span>
              <template v-for="c in ['tools', 'vision', 'reasoning']" :key="c"><span v-if="r.caps?.[c]" class="pill">{{ $t(`ai.cmp.cap.${c}`) }}</span></template>
            </div>
          </div>
        </div>
        <p v-if="chosen.length < 2" class="empty-state">{{ $t('ai.cmp.needTwo') }}</p>
        <template v-else>
          <h3 class="sec">{{ $t('ai.cmp.glance') }}</h3>
          <p class="verdict">{{ !shared.keys.length ? $t('ai.cmp.noCommon') : verdict ? $t('ai.cmp.better', { name: verdict }) : $t('ai.cmp.tooClose') }}</p>
          <p v-if="shared.keys.length" class="muted small note">{{ sharedNote }}</p>
          <div v-for="g in glance" :key="g.k" class="brow">
            <div class="blab muted small">{{ g.label }}</div>
            <div class="heads" :style="{ '--n': chosen.length }">
              <div v-for="(r, i) in chosen" :key="r.id" class="bcell">
                <template v-if="g.txt(r, i)">
                  <span class="gv" :class="{ best: best(g.raw, g.raw[i], g.low) }"><span v-if="best(g.raw, g.raw[i], g.low)" class="mk" />{{ g.txt(r, i) }}</span>
                  <div v-if="g.sub && g.sub(r)" class="faint small">{{ g.sub(r) }}</div>
                </template>
                <span v-else class="faint">{{ $t('ai.cmp.na') }}</span>
              </div>
            </div>
          </div>

          <template v-if="hw">
            <h3 class="sec">{{ $t('ai.cmp.secHardware') }}</h3>
            <div class="brow">
              <div class="blab muted small">{{ $t('ai.tps') }}</div>
              <div class="heads" :style="{ '--n': chosen.length }"><div v-for="r in chosen" :key="r.id" class="bcell"><span :class="{ best: best(chosen.map(c => c.tokens_per_s), r.tokens_per_s) }">{{ r.tokens_per_s ?? $t('ai.cmp.na') }}</span></div></div>
            </div>
            <div class="brow">
              <div class="blab muted small">{{ $t('ai.ttft') }}</div>
              <div class="heads" :style="{ '--n': chosen.length }"><div v-for="r in chosen" :key="r.id" class="bcell"><span :class="{ best: best(chosen.map(c => c.ttft_ms), r.ttft_ms, true) }">{{ ms(r.ttft_ms) }}</span></div></div>
            </div>
          </template>
        </template>
      </template>
      <p class="faint small src">{{ $t('ai.cmp.sources', { list: srcLine }) }}</p>
    </template>
  </Panel>
</template>

<style scoped>
.sk-wrap { display: grid; gap: 14px; }
.bar { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.bar.nowrap { flex-wrap: nowrap; }
.search { width: 100%; margin-bottom: 12px; }
.tbl { max-height: 72vh; overflow-y: auto; border: 1px solid var(--line); border-radius: var(--radius-sm); }
.cmp { border-collapse: separate; border-spacing: 0; width: 100%; }
.cmp th, .cmp td { white-space: nowrap; padding: 11px 12px; border-bottom: 1px solid var(--line); vertical-align: middle; }
.cmp tbody tr:last-child td { border-bottom: 0; }
.cmp thead th { position: sticky; top: 0; z-index: 2; background: var(--panel); }
.cmp .stick { position: sticky; left: 0; background: var(--panel); z-index: 1; white-space: normal; min-width: 190px; max-width: 240px; }
.cmp thead .stick { z-index: 3; }
.cmp .sc { min-width: 92px; }
.sortb { color: inherit; font-size: inherit; }
.row { cursor: pointer; }
.row.unscored { opacity: .55; }
.chartbox { background: var(--panel-2); border: 1px solid var(--line); border-radius: var(--radius); padding: 12px; margin-bottom: 12px; }
.row.sel td { background: var(--accent-soft); }
.who { display: flex; align-items: center; gap: 10px; }
.rk { min-width: 22px; text-align: right; }
.who-t { min-width: 0; }
.nm { font-weight: 600; overflow-wrap: anywhere; display: flex; align-items: center; gap: 6px; }
.tick { color: var(--accent); flex: none; }
.sv { font-weight: 500; }
.mini { height: 4px; background: var(--accent-soft); border-radius: 2px; margin-top: 5px; overflow: hidden; }
.mini-f { height: 100%; background: var(--accent); border-radius: 2px; }
.gap { margin-left: 4px; }
.more { text-align: center; margin-top: 14px; }
.src { margin: 18px 0 0; }
.note { margin: -2px 0 8px; }

.combo { position: relative; margin-bottom: 14px; }
.combo-in { position: relative; }
.combo-in .search { margin: 0; padding-left: 34px; }
.combo-ic { position: absolute; left: 11px; top: 50%; transform: translateY(-50%); color: var(--faint); pointer-events: none; }
.pop { position: absolute; z-index: 20; left: 0; right: 0; top: calc(100% + 4px); max-height: 40vh; overflow-y: auto; overscroll-behavior: contain; -webkit-overflow-scrolling: touch; background: var(--panel); border: 1px solid var(--line-2); border-radius: var(--radius-sm); box-shadow: 0 8px 24px rgba(0, 0, 0, .35); }
.pop-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; width: 100%; min-height: 44px; padding: 8px 12px; background: none; border: 0; border-top: 1px solid var(--line); color: var(--text); font: inherit; text-align: left; cursor: pointer; }
.pop-row:first-child { border-top: 0; }
.pop-row.act { background: var(--panel-2); }
.pop-row.picked { background: var(--accent-soft); cursor: default; opacity: .8; }
.pop-t { display: flex; flex-direction: column; min-width: 0; }
.pop-p { display: flex; align-items: center; gap: 6px; flex: none; }
.pop-note { padding: 12px; color: var(--muted); font-size: 13px; text-align: center; }

.heads { display: grid; grid-template-columns: repeat(var(--n, 2), minmax(0, 1fr)); gap: 10px; }
.hcard { position: relative; background: var(--panel-2); border: 1px solid var(--line); border-radius: var(--radius); padding: 12px; display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.hcard .nm { padding-right: 30px; }
.hcard .rm { position: absolute; top: 4px; right: 4px; }
.verdict { font-size: 18px; font-weight: 600; margin: 0 0 6px; }
.gv { display: inline-flex; align-items: center; gap: 6px; font-size: 15px; }
.mk { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); flex: none; }
.pills { display: flex; gap: 4px; flex-wrap: wrap; }
.brow { padding: 10px 0; border-bottom: 1px solid var(--line); }
.brow:last-child { border-bottom: 0; }
.blab { margin-bottom: 6px; }
.bcell { font-size: 13px; min-width: 0; overflow-wrap: anywhere; }
.best { color: var(--accent); font-weight: 600; }
@media (pointer: coarse) {
  .hcard .rm { min-width: 32px; min-height: 32px; }
  .sortb { min-height: 32px; }
  .chip { min-height: 32px; }
}
@media (max-width: 640px) {
  .heads { gap: 8px; }
  .hcard { padding: 10px; }
}
</style>
