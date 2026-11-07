import { randomBytes } from 'node:crypto'
import { cleanWidget, WIDGET_LOOKS, WIDGET_SIZES, WIDGET_SOURCES, WidgetError } from '../../app/utils/widgets'

/**
 * "Describe a widget": the same mechanism as the Designs add-on's "Describe a look": a tool-less `claude -p` on the
 * host started through the agent's /designs/ai/start (prompt + JSON schema, one systemd unit per job), polled with
 * /designs/ai/job. The answer is cleaned by cleanWidget before the builder previews it; nothing is saved until Save.
 */
const agentCall = <T = any>(path: string, opts: UpstreamOpts = {}) => {
  const { agentUrl, agentToken } = useRuntimeConfig()
  return upstream<T>('agent', agentUrl, agentToken, path, 30_000, opts)
}

export const WIDGET_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['name', 'size', 'look', 'source'],
  properties: {
    name: { type: 'string', maxLength: 40 },
    size: { type: 'string', enum: WIDGET_SIZES },
    look: { type: 'string', enum: WIDGET_LOOKS },
    source: {
      type: 'object',
      additionalProperties: false,
      required: ['type'],
      properties: {
        type: { type: 'string', enum: [...WIDGET_SOURCES, 'none'] },
        path: { type: 'string' }, pick: { type: 'string' }, name: { type: 'string' }, id: { type: 'string' },
      },
    },
    format: {
      type: 'object',
      additionalProperties: false,
      properties: { prefix: { type: 'string' }, suffix: { type: 'string' }, decimals: { type: 'integer' }, max: { type: 'number' }, field: { type: 'string' } },
    },
    button: {
      type: 'object',
      additionalProperties: false,
      properties: { label: { type: 'string' }, path: { type: 'string' }, body: { type: 'object', additionalProperties: { type: 'string' } } },
    },
  },
}

const REFERENCE = `
A Home widget is declarative JSON, never code. Fields:
- name (<= 40 chars), size S|M|L (S = one cell, M = two wide, L = two wide and tall)
- look: number (one big value), sparkline (a list of numbers, or a number that is tracked over time), list (an array
  shown as lines), gauge (a number 0..format.max drawn as a bar), text (a string or note body), button
- source.type, one of:
  metric  {pick}: dot-path into the Metrics data (/api/overview), e.g. host.cpu, host.mem.used, gpu.util, cts[0].status.
          Arrays can be searched: services[name=Jellyfin].up
  service {name}: health of one app tile (Up/Down), name exactly as in the services list below
  api     {path, pick?}: a GET path starting with /api/ (no ".."), optional dot-path into its JSON answer
  task    {id}: the latest answer of a scheduled task, id from the tasks list below
  note    {id}: the body of a note, id from the notes list below
  Use "none" only for buttons.
- format (optional): prefix, suffix (units like "%" or " GB"), decimals, max (for gauge), field (which key of each array item to show/plot)
- button (look "button" only): {label, path, body}. Only these targets exist: path "/api/chat-tasks" with body {"op":"run","id":"<task id>"}
  (run a scheduled task now) or path "/api/net/speedtest" with no body. Nothing else may be used.
Never write emoji or decorative symbols. Keep names short and plain.
`

export async function widgetAiStart(ask: string, base: any, ctx: { services: string[], tasks: any[], notes: any[] }) {
  const job = randomBytes(8).toString('hex')
  const prompt = `You design one small widget for a home-server dashboard. Request:
"""${ask.slice(0, 1500)}"""
${REFERENCE}
Services: ${ctx.services.join(', ') || 'none'}
Tasks: ${ctx.tasks.map(t => `${t.id} (${t.title})`).join('; ') || 'none'}
Notes: ${ctx.notes.map(n => `${n.id} (${n.title})`).join('; ') || 'none'}
${base ? `The widget it starts from (keep what the request does not change): ${JSON.stringify(base).slice(0, 2000)}` : ''}
Answer with the JSON object only.`
  await agentCall('/designs/ai/start', { method: 'POST', body: { job, prompt, schema: WIDGET_SCHEMA } })
  return { job }
}

export async function widgetAiJob(job: string, id: string) {
  if (!/^[a-f0-9]{16}$/.test(job)) throw createError({ statusCode: 400, statusMessage: 'bad job' })
  const r = await agentCall<any>(`/designs/ai/job?id=${job}`)
  if (r.state !== 'done') return r
  try {
    const raw = r.result ?? {}
    if (raw.source?.type === 'none' && raw.look !== 'button') throw new WidgetError('Claude did not give a data source')
    return { state: 'done', secs: r.secs, widget: cleanWidget({ ...raw, id }) }
  } catch (e: any) {
    return { state: 'failed', error: e instanceof WidgetError ? `Claude's answer was not a valid widget: ${e.message}` : 'bad answer' }
  }
}
