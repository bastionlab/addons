/**
 * Widget definitions: declarative JSON, never code. The same checks run in the builder (client) and in every
 * /api/widgets route (server imports this file by relative path), so what the server fetches was always
 * validated here. Pure functions only: no Nuxt auto-imports.
 */
export type WidgetSize = 'S' | 'M' | 'L'
export type WidgetLook = 'number' | 'sparkline' | 'list' | 'gauge' | 'text' | 'button' | 'component'
export type SourceType = 'api' | 'metric' | 'service' | 'task' | 'note' | 'none'

export interface WidgetSource { type: SourceType, path?: string, pick?: string, name?: string, id?: string }
export interface WidgetFormat { prefix?: string, suffix?: string, decimals?: number, max?: number, field?: string }
export interface WidgetButton { label: string, path: string, body?: Record<string, string> }
export interface WidgetDef {
  id: string, name: string, size: WidgetSize, look: WidgetLook, source: WidgetSource
  format?: WidgetFormat, button?: WidgetButton
  /** packs only: the Vue component a pack ships (Widget<Name>) and the pack's add-on id */
  component?: string, pack?: string
}

export const WIDGET_SIZES: WidgetSize[] = ['S', 'M', 'L']
export const WIDGET_LOOKS: WidgetLook[] = ['number', 'sparkline', 'list', 'gauge', 'text', 'button']
export const WIDGET_SOURCES: SourceType[] = ['api', 'metric', 'service', 'task', 'note']
/** the only POST targets a button may fire (after a confirm step); body values are fixed strings */
export const BUTTON_TARGETS: Record<string, string[]> = {
  '/api/chat-tasks': ['op', 'id'], // { op: 'run', id } = run a scheduled task now
  '/api/net/speedtest': [],
}
export const MAX_WIDGETS = 24
export const MAX_RESULT = 50_000 // chars of JSON a picked value may have

const SEG = /^[A-Za-z0-9_-]+(\[(\d+|[A-Za-z0-9_-]+=[^\]\s]{1,40})\])*$/
const BAD_SEG = new Set(['__proto__', 'constructor', 'prototype'])
/** a dot-path into JSON: a.b[0].c, or an array lookup by field: services[name=Jellyfin].up */
export function okPick(p: any): p is string {
  if (typeof p !== 'string' || !p || p.length > 120) return false
  return p.split('.').every(s => SEG.test(s) && !BAD_SEG.has(s.replace(/\[.*$/, '')))
}
/** a GET path inside the dashboard's own API; no traversal, no auth/user/secret routes, not this add-on */
export function okApiPath(p: any): p is string {
  if (typeof p !== 'string' || p.length > 200) return false
  if (!/^\/api\/[A-Za-z0-9/_\-.?=&,:]+$/.test(p) || p.includes('..') || p.includes('//')) return false
  return !/^\/api\/(widgets|auth|users|account|settings|backup|synced)(\/|\?|$)/.test(p)
}

export function pickPath(data: any, path: string): any {
  let cur = data
  for (const seg of path.split('.')) {
    const name = /^[^[]+/.exec(seg)?.[0] ?? ''
    if (cur == null || typeof cur !== 'object') return undefined
    cur = cur[name]
    for (const m of seg.matchAll(/\[([^\]]+)\]/g)) {
      const q = m[1]!
      if (cur == null || typeof cur !== 'object') return undefined
      if (/^\d+$/.test(q)) cur = (cur as any)[Number(q)]
      else if (Array.isArray(cur)) { const [k, v] = q.split('=') as [string, string]; cur = cur.find(x => x && String(x[k]) === v) }
      else return undefined
    }
  }
  return cur
}

const str = (v: any, n: number) => (typeof v === 'string' ? v.trim().slice(0, n) : '')
export class WidgetError extends Error {}

/** the cleaned definition, or a WidgetError saying what is wrong; unknown keys are dropped. `packOk` allows look "component" */
export function cleanWidget(raw: any, opts: { packOk?: boolean } = {}): WidgetDef {
  if (!raw || typeof raw !== 'object' || JSON.stringify(raw).length > 4000) throw new WidgetError('Not a widget definition')
  const id = str(raw.id, 40)
  if (!/^[a-z0-9][a-z0-9-]{0,39}$/.test(id)) throw new WidgetError('id: lowercase letters, digits and dashes')
  const name = str(raw.name, 40)
  if (!name) throw new WidgetError('name is empty')
  const size: WidgetSize = WIDGET_SIZES.includes(raw.size) ? raw.size : 'S'
  const look = raw.look
  const isComp = look === 'component'
  if (isComp ? !opts.packOk : !WIDGET_LOOKS.includes(look)) throw new WidgetError(`unknown look "${String(look).slice(0, 20)}"`)
  const def: WidgetDef = { id, name, size, look, source: { type: 'none' } }
  const fm = raw.format
  if (fm && typeof fm === 'object') {
    def.format = {
      ...(str(fm.prefix, 12) && { prefix: str(fm.prefix, 12) }), ...(str(fm.suffix, 12) && { suffix: str(fm.suffix, 12) }),
      ...(Number.isFinite(Number(fm.decimals)) && fm.decimals !== '' && fm.decimals != null && { decimals: Math.min(6, Math.max(0, Math.round(Number(fm.decimals)))) }),
      ...(Number(fm.max) > 0 && { max: Number(fm.max) }),
      ...(okPick(fm.field) && { field: fm.field }),
    }
  }
  if (isComp) {
    if (!/^Widget[A-Za-z0-9]{1,40}$/.test(String(raw.component))) throw new WidgetError('component must be Widget<Name>')
    def.component = raw.component
    if (raw.pack) def.pack = str(raw.pack, 40)
    return def
  }
  if (look === 'button') {
    const b = raw.button
    const path = typeof b?.path === 'string' ? b.path.split('?')[0]! : ''
    const keys = BUTTON_TARGETS[path]
    if (!keys) throw new WidgetError('button: this action is not allowed')
    const body: Record<string, string> = {}
    for (const k of keys) body[k] = str(b.body?.[k], 80)
    if (path === '/api/chat-tasks' && (body.op !== 'run' || !body.id)) throw new WidgetError('button: choose a task to run')
    def.button = { label: str(b.label, 30) || name, path, ...(keys.length && { body }) }
    return def
  }
  const s = raw.source ?? {}
  const type: SourceType = s.type
  if (!WIDGET_SOURCES.includes(type)) throw new WidgetError(`unknown source "${String(type).slice(0, 20)}"`)
  const src: WidgetSource = { type }
  if (type === 'api') {
    if (!okApiPath(s.path)) throw new WidgetError('api path must be a /api/ path without ..')
    src.path = s.path
  }
  if (type === 'service') {
    src.name = str(s.name, 60)
    if (!src.name || !/^[\w .+-]{1,60}$/.test(src.name)) throw new WidgetError('pick a service')
    return { ...def, source: src }
  }
  if (type === 'task') {
    src.id = str(s.id, 40)
    if (!/^[A-Za-z0-9_-]{1,40}$/.test(src.id)) throw new WidgetError('pick a task')
    return { ...def, source: src }
  }
  if (type === 'note') {
    src.id = String(Math.round(Number(s.id)))
    if (!/^\d{1,9}$/.test(src.id)) throw new WidgetError('pick a note')
    return { ...def, source: src }
  }
  if (s.pick != null && s.pick !== '') {
    if (!okPick(s.pick)) throw new WidgetError('pick: a dot-path like a.b[0].c')
    src.pick = s.pick
  } else if (type === 'metric') throw new WidgetError('pick the metric path')
  return { ...def, source: src }
}

export function fmtNum(v: any, f?: WidgetFormat) {
  const n = Number(v)
  const s = Number.isFinite(n) ? (f?.decimals != null ? n.toFixed(f.decimals) : String(Math.round(n * 100) / 100)) : String(v ?? '–')
  return `${f?.prefix ?? ''}${s}${f?.suffix ?? ''}`
}
/** a list/sparkline value as plain parts */
export function asList(v: any, f?: WidgetFormat): string[] {
  const a = Array.isArray(v) ? v : v && typeof v === 'object' ? Object.entries(v).map(([k, x]) => `${k}: ${typeof x === 'object' ? '' : x}`) : v == null ? [] : [v]
  return a.slice(0, 30).map(x => (x && typeof x === 'object' ? String((f?.field ? pickPath(x, f.field) : x.name ?? x.title ?? JSON.stringify(x)) ?? '') : String(x)).slice(0, 120))
}
export function asSeries(v: any, f?: WidgetFormat): number[] {
  const a = Array.isArray(v) ? v : []
  return a.slice(-60).map(x => Number(x && typeof x === 'object' ? (f?.field ? pickPath(x, f.field) : Object.values(x).find(y => typeof y === 'number')) : x)).filter(Number.isFinite)
}
