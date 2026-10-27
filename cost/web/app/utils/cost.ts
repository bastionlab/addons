/** numbers for the Cost page and Home card; everything is derived from /api/cost/summary */
export interface CostRate { in: number, out: number, cache_read: number, cache_write: number }
export interface CostModel extends CostRate { usd: number }
export interface CostDay {
  day: string
  claude: { usd: number, by_model: Record<string, CostModel>, turns: number, learn_usd: number }
  local: { by_job: Record<string, { calls: number, in: number, out: number }> }
  gpu_wh: Record<string, number>
  server_wh: number
}
export interface CostSummary {
  settings: { eur_kwh: number, usd_eur: number, idle_w: number, max_w: number }
  prices: Record<string, CostRate>
  days: CostDay[]
  plan: { t: number, five_h: number, week: number }[]
  proxy: { ok: boolean, since: string | null }
}

/** chart palette (the one place hex colours are fine); stable order so a model keeps its colour */
export const COST_COLORS = ['#7c9cff', '#f0a35e', '#5cc9a7', '#e46f8e', '#b58cf2', '#d6c35a', '#6fc3e6', '#9aa3b2']
export const GPU_CLASSES = ['ollama', 'speech', 'games', 'idle', 'other'] as const

export const costFamily = (model: string) => /opus/i.test(model) ? 'opus' : /sonnet/i.test(model) ? 'sonnet' : /haiku/i.test(model) ? 'haiku' : model
export const costShort = (model: string) => model.replace(/^claude-/, '').replace(/-\d{8}$/, '')

const M = 1e6
export function costAt(r: CostRate | undefined, m: { in?: number, out?: number, cache_read?: number, cache_write?: number }) {
  if (!r) return 0
  return ((m.in ?? 0) * r.in + (m.out ?? 0) * r.out + (m.cache_read ?? 0) * r.cache_read + (m.cache_write ?? 0) * r.cache_write) / M
}
export const costTokens = (m: { in?: number, out?: number, cache_read?: number, cache_write?: number }) => (m.in ?? 0) + (m.out ?? 0) + (m.cache_read ?? 0) + (m.cache_write ?? 0)

export const costGpuWh = (d: CostDay) => Object.values(d.gpu_wh ?? {}).reduce((a, b) => a + (b || 0), 0)
export const costLocalTokens = (d: CostDay) => Object.values(d.local?.by_job ?? {}).reduce((a, j) => a + (j.in || 0) + (j.out || 0), 0)

/** API price of local tokens: [at Haiku rates, at Sonnet rates] in USD */
export function costLocalApi(s: CostSummary, d: CostDay): [number, number] {
  let i = 0, o = 0
  for (const j of Object.values(d.local?.by_job ?? {})) { i += j.in || 0; o += j.out || 0 }
  return [costAt(s.prices.haiku, { in: i, out: o }), costAt(s.prices.sonnet, { in: i, out: o })]
}

/** what Haiku/Sonnet tokens would have cost at the Opus rate, minus what they cost */
export function costSaved(s: CostSummary, d: CostDay) {
  let v = 0
  for (const [m, x] of Object.entries(d.claude?.by_model ?? {})) {
    const f = costFamily(m)
    if (f === 'haiku' || f === 'sonnet') v += costAt(s.prices.opus, x) - x.usd
  }
  return v
}

export function costTotals(s: CostSummary, days: CostDay[]) {
  const eur = s.settings.usd_eur, kwh = s.settings.eur_kwh
  let usd = 0, saved = 0, lo = 0, hi = 0, gpuWh = 0, srvWh = 0, ollamaWh = 0
  for (const d of days) {
    usd += d.claude?.usd ?? 0
    saved += costSaved(s, d)
    const [a, b] = costLocalApi(s, d)
    lo += a; hi += b
    gpuWh += costGpuWh(d); srvWh += d.server_wh || 0; ollamaWh += d.gpu_wh?.ollama || 0
  }
  return {
    usd, eur: usd * eur, saved, savedEur: saved * eur,
    apiLo: lo * eur, apiHi: hi * eur, gpuWh, srvWh,
    // gpu_wh covers the GPU incl. its idle draw; server_wh is the rest of the box (idle_w/max_w exclude the GPU)
    power: ((gpuWh + srvWh) / 1000) * kwh, ollamaEur: (ollamaWh / 1000) * kwh,
  }
}

/** days of the current calendar month (the agent's day strings are local dates) */
export function costMonthDays(s: CostSummary | null | undefined, now = new Date()) {
  const p = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  return (s?.days ?? []).filter(d => d.day.startsWith(p))
}
export const costHasData = (s: CostSummary | null | undefined) =>
  !!s?.days?.some(d => (d.claude?.usd ?? 0) > 0 || costLocalTokens(d) > 0 || costGpuWh(d) > 0 || (d.server_wh ?? 0) > 0)

export const costUsd = (n: number, digits = 2) => `$${n.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })}`
export const costKwh = (wh: number) => `${(wh / 1000).toLocaleString('de-DE', { maximumFractionDigits: 2 })} kWh`
export function costTok(n: number) {
  const a = Math.abs(n)
  return a >= 1e9 ? `${(n / 1e9).toFixed(1)}B` : a >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : a >= 1e3 ? `${(n / 1e3).toFixed(a >= 1e5 ? 0 : 1)}k` : String(Math.round(n))
}
