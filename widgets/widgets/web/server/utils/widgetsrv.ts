import { existsSync, readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import type { H3Event } from 'h3'
import { cleanWidget, MAX_RESULT, okApiPath, pickPath, WidgetError, type WidgetDef } from '../../app/utils/widgets'

/**
 * Widgets, server side: every definition is cleaned again here (the client's check is a convenience), data comes
 * from the dashboard's own API called in-process with the viewer's own headers, so a widget can never read more
 * than the signed-in owner could open anyway. Nothing here stores anything: definitions live in useSynced.
 */
export const bad = (code: number, msg: string) => createError({ statusCode: code, statusMessage: msg })

export function parseDef(raw: any, packOk = false): WidgetDef {
  try { return cleanWidget(raw, { packOk }) } catch (e) {
    if (e instanceof WidgetError) throw bad(400, e.message)
    throw e
  }
}

/** the viewer's own request headers (cookie, tailnet login, origin …) so the inner call passes the same auth middleware */
function inner(event: H3Event) {
  const h: Record<string, string> = {}
  for (const [k, v] of Object.entries(event.node.req.headers)) {
    if (typeof v === 'string' && !['content-length', 'content-type', 'accept-encoding', 'connection', 'transfer-encoding'].includes(k)) h[k] = v
  }
  return h
}
async function get(event: H3Event, path: string) {
  if (!okApiPath(path) && path !== '/api/overview') throw bad(400, 'bad api path')
  const r = await $fetch<any>(path, { headers: inner(event), timeout: 8000, retry: 0 }).catch((e: any) => {
    throw bad(502, `${path}: ${e?.statusMessage || e?.statusText || e?.message || 'failed'}`.slice(0, 200))
  })
  if (JSON.stringify(r ?? null).length > 2_000_000) throw bad(413, 'response too big')
  return r
}

/** the current value of a definition's source: { value, at, label? } */
export async function widgetValue(event: H3Event, d: WidgetDef) {
  const s = d.source
  let value: any
  let label: string | undefined
  if (s.type === 'api') {
    const r = await get(event, s.path!)
    value = s.pick ? pickPath(r, s.pick) : r
  } else if (s.type === 'metric') {
    value = pickPath(await get(event, '/api/overview'), s.pick!)
  } else if (s.type === 'service') {
    // service health lives in /api/overview (services[], each probed: name, up, ms); the same data as the Metrics page
    const sv = ((await get(event, '/api/overview'))?.services ?? []).find((x: any) => x?.name === s.name)
    if (!sv) throw bad(404, `no service "${s.name}"`)
    value = sv.up ? 'Up' : 'Down'
    label = sv.ms != null ? `${sv.ms} ms` : undefined
  } else if (s.type === 'task') {
    const t = ((await get(event, '/api/chat-tasks'))?.tasks ?? []).find((x: any) => x?.id === s.id)
    if (!t) throw bad(404, 'no such task')
    const turns = chatById(t.chat)?.turns ?? []
    const last = [...turns].reverse().find((x: any) => x.a)
    value = last?.a ? String(last.a).replace(/^ALL-OK[:\s-]*/, '').trim() : ''
    label = t.title
  } else if (s.type === 'note') {
    const n = ((await get(event, '/api/notes'))?.notes ?? []).find((x: any) => String(x?.id) === s.id)
    if (!n) throw bad(404, 'no such note')
    value = n.body
    label = n.title
  }
  if (JSON.stringify(value ?? null).length > MAX_RESULT) throw bad(413, 'the picked value is too big, pick a smaller part')
  return { value: value ?? null, label, at: Date.now() }
}

/** run a button: the target was allowlisted by cleanWidget; the viewer's headers go along (same-origin check included) */
export async function widgetPress(event: H3Event, d: WidgetDef) {
  const b = d.button
  if (d.look !== 'button' || !b) throw bad(400, 'not a button')
  return $fetch<any>(b.path, { method: 'POST', body: b.body ?? {}, headers: inner(event), timeout: 15_000, retry: 0 })
    .catch((e: any) => { throw bad(502, String(e?.statusMessage || e?.message || 'failed').slice(0, 200)) })
}

// ---- widget packs: add-ons with `kind: widget` in addon.yaml and a widget.json next to it -------------------

const dirs = () => [process.env.DASH_ADDONS_DIR, '/opt/dash/addons', join(process.cwd(), 'addons'), join(process.cwd(), '../addons')]
  .filter((d): d is string => !!d && existsSync(d))

/** installed, switched-on widget packs with their cleaned definitions (invalid ones are listed as errors, not dropped silently) */
export function widgetPacks() {
  const root = dirs()[0]
  if (!root) return []
  const off = new Set(addonsOff())
  const out: { pack: string, name: string, version: string, defs: WidgetDef[], errors: string[] }[] = []
  for (const d of readdirSync(root)) {
    if (!/^[a-z][a-z0-9-]{1,30}$/.test(d) || off.has(d)) continue
    const yaml = join(root, d, 'addon.yaml'), file = join(root, d, 'widget.json')
    if (!existsSync(yaml) || !existsSync(file)) continue
    const y = readFileSync(yaml, 'utf8')
    if (!/^kind:\s*widget\s*$/m.test(y)) continue
    let list: any[] = []
    const errors: string[] = []
    try {
      const j = JSON.parse(readFileSync(file, 'utf8'))
      list = Array.isArray(j) ? j : Array.isArray(j?.widgets) ? j.widgets : [j]
    } catch { errors.push('widget.json is not valid JSON') }
    const defs: WidgetDef[] = []
    for (const raw of list.slice(0, 24)) {
      try {
        const x = cleanWidget({ ...raw, id: `${d}-${raw?.id}` }, { packOk: true })
        defs.push(x.look === 'component' ? { ...x, pack: d } : x)
      } catch (e: any) { errors.push(`${raw?.id ?? '?'}: ${e.message}`) }
    }
    out.push({
      pack: d, name: /^name:\s*(.+)$/m.exec(y)?.[1]?.replace(/^["']|["']$/g, '') ?? d,
      version: /^version:\s*(.+)$/m.exec(y)?.[1]?.trim() ?? '', defs, errors,
    })
  }
  return out
}
