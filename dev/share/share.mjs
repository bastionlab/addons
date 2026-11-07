// dash-share: the only thing in CT 104 the internet can reach (Tailscale Funnel :8443 → 127.0.0.1:3100).
// Public side: /s/<token> checks a link (single use, expiry, revoked), sets a session cookie and from then on
// proxies that browser to the one dev-box preview the link points at (http + websockets). Nothing else answers.
// Control side: 127.0.0.1:3101, only the dashboard app in this CT talks to it (list / create / revoke / delete).
import http from 'node:http'
import net from 'node:net'
import fs from 'node:fs'
import crypto from 'node:crypto'
import { execFile } from 'node:child_process'

const DIR = process.env.SHARE_DIR || '/var/lib/dash-share'
const FILE = `${DIR}/links.json`
const PUBLIC_PORT = 3100, CTL_PORT = 3101
const COOKIE = 'bastion_share'
const SESSION_MS = 12 * 3600e3 // a visit lasts at most this long (or until the link ends), then open the link again
const TARGET_RE = /^192\.168\.\d{1,3}\.\d{1,3}:\d{2,5}$|^10\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}$/

fs.mkdirSync(DIR, { recursive: true, mode: 0o700 })
let db = { links: [], sessions: {} }
try { db = JSON.parse(fs.readFileSync(FILE, 'utf8')) } catch {}
let dirty = false
const save = () => { dirty = true }
setInterval(() => {
  const now = Date.now()
  for (const [sid, s] of Object.entries(db.sessions)) if (s.expires < now) { delete db.sessions[sid]; dirty = true }
  if (!dirty) return
  dirty = false
  fs.writeFileSync(FILE + '.tmp', JSON.stringify(db, null, 1), { mode: 0o600 })
  fs.renameSync(FILE + '.tmp', FILE)
}, 2000)

const live = (l, now = Date.now()) => !l.revoked && (!l.expires || l.expires > now)
const status = (l) => l.revoked ? 'revoked' : l.expires && l.expires <= Date.now() ? 'expired' : l.once && l.uses ? 'used' : 'active'

function page(res, code, title, text) {
  res.writeHead(code, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store', 'x-robots-tag': 'noindex' })
  res.end(`<!doctype html><meta name=viewport content="width=device-width,initial-scale=1"><title>${title}</title>
<body style="font:16px system-ui;background:#0f1115;color:#d5d9e0;display:grid;place-items:center;min-height:90vh;margin:0">
<div style="max-width:340px;text-align:center"><h2 style="margin:0 0 8px">${title}</h2><p style="color:#8a93a3">${text}</p></div>`)
}

function cookieOf(req) {
  const m = (req.headers.cookie || '').match(new RegExp(`(?:^|;\\s*)${COOKIE}=([A-Za-z0-9_-]+)`))
  return m?.[1]
}
// cookies are not split by port, so the dashboard's own (:443) would ride along here: the app only ever sees
// cookies it set itself through this gate, stored under a `bs_` prefix
const PREFIX = 'bs_'
const inCookies = (c = '') => c.split(/;\s*/).filter(p => p.startsWith(PREFIX)).map(p => p.slice(PREFIX.length)).join('; ')
const outCookie = c => PREFIX + String(c).trim().replace(/;\s*domain=[^;]*/i, '')

/** the link this browser's session belongs to, if both are still good */
function linkFor(req) {
  const sid = cookieOf(req)
  const s = sid && db.sessions[sid]
  if (!s || s.expires < Date.now()) return null
  const l = db.links.find(x => x.id === s.link)
  return l && live(l) ? l : null
}

function headersFor(req, l) {
  const h = { ...req.headers }
  for (const k of Object.keys(h)) if (/^(tailscale-|x-forwarded-|forwarded$|x-real-ip$)/i.test(k)) delete h[k]
  const c = inCookies(h.cookie)
  if (c) h.cookie = c; else delete h.cookie
  h.host = l.target // dev servers (Vite) refuse hosts they don't know
  h['x-forwarded-proto'] = 'https'
  if (req.headers.host) h['x-forwarded-host'] = req.headers.host
  if (h.origin) h.origin = `http://${l.target}`
  return h
}

// --- shared files: the agent (host) streams them. This process holds only a narrow token that opens GET /files/pub
// (never the agent's main one), from /etc/dash-share/agent.env, which the Files add-on writes; read per request so a
// rotation applies at once. It runs as the unprivileged dash-share user and cannot read the dashboard's /etc/dash.env.
function agentEnv() {
  let txt = ''
  try { txt = fs.readFileSync(process.env.DASH_SHARE_ENV || '/etc/dash-share/agent.env', 'utf8') } catch {}
  const get = (k) => (txt.match(new RegExp(`^${k}=(.*)$`, 'm'))?.[1] || '').trim().replace(/^["']|["']$/g, '')
  return { url: get('DASH_AGENT_URL').replace(/\/$/, ''), token: get('DASH_FILES_TOKEN') }
}
const gone = (res) => { res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'no-store', 'x-robots-tag': 'noindex' }); res.end('Link expired or not found') }
function sendFile(req, res, token, dl) {
  const { url: AGENT_URL, token: AGENT_TOKEN } = agentEnv()
  if (!AGENT_URL || !AGENT_TOKEN) return gone(res)
  const h = { authorization: `Bearer ${AGENT_TOKEN}` }
  if (req.headers.range) h.range = req.headers.range
  if (req.headers['if-range']) h['if-range'] = req.headers['if-range']
  const unavailable = () => res.headersSent ? res.destroy() : page(res, 502, 'Unavailable', 'The file could not be fetched right now. Try again in a bit.')
  let up
  try { up = http.request(`${AGENT_URL}/files/pub?t=${encodeURIComponent(token)}${dl ? '&dl=1' : ''}`, { method: 'GET', headers: h }, (r) => {
    if (r.statusCode === 404 || r.statusCode === 403 || r.statusCode === 401) { r.resume(); return gone(res) }
    const out = { 'cache-control': 'no-store', 'x-robots-tag': 'noindex', 'x-content-type-options': 'nosniff' }
    for (const k of ['content-type', 'content-length', 'content-range', 'accept-ranges', 'content-disposition', 'content-security-policy', 'etag', 'last-modified']) if (r.headers[k]) out[k] = r.headers[k]
    res.writeHead(r.statusCode || 502, out)
    if (req.method === 'HEAD') { r.destroy(); return res.end() } // the agent only speaks GET
    r.pipe(res)
    res.on('close', () => r.destroy())
  }) } catch { return unavailable() } // a bad URL in the env file must not take the gate down
  up.on('error', unavailable)
  req.on('close', () => up.destroy())
  up.end()
}

// --- public ------------------------------------------------------------------
const pub = http.createServer((req, res) => {
  const url = req.url || '/'
  const m = url.match(/^\/s\/([A-Za-z0-9_-]{20,})\/?(?:\?.*)?$/)
  if (m) {
    const l = db.links.find(x => x.token === m[1])
    if (!l || !live(l)) return page(res, 410, 'Link expired', 'This link was revoked or has run out. Ask for a new one.')
    if (l.once && l.uses) return page(res, 410, 'Link already used', 'This was a one-time link and it has been opened already.')
    l.uses = (l.uses || 0) + 1
    l.lastUsed = Date.now()
    const sid = crypto.randomBytes(24).toString('base64url')
    const expires = Math.min(Date.now() + SESSION_MS, l.expires || Infinity)
    db.sessions[sid] = { link: l.id, expires }
    save()
    res.writeHead(302, {
      location: '/', 'cache-control': 'no-store',
      'set-cookie': `${COOKIE}=${sid}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${Math.floor((expires - Date.now()) / 1000)}`,
    })
    return res.end()
  }
  // /f/<token>: a file shared from the Files tab, streamed from the agent (which checks the token); Range passes through
  const f = url.match(/^\/f\/([A-Za-z0-9_-]{16,})\/?(?:\?(.*))?$/)
  if (f && (req.method === 'GET' || req.method === 'HEAD')) return sendFile(req, res, f[1], new URLSearchParams(f[2] || '').get('dl') === '1')
  const l = linkFor(req)
  if (!l) return page(res, 404, 'Nothing here', 'Open the link you were sent to see the project.')
  const [host, port] = l.target.split(':')
  const up = http.request({ host, port: +port, method: req.method, path: url, headers: headersFor(req, l) }, (r) => {
    const h = { ...r.headers }
    if (h.location) h.location = String(h.location).replace(`http://${l.target}`, '')
    if (h['set-cookie']) h['set-cookie'] = h['set-cookie'].map(outCookie)
    res.writeHead(r.statusCode || 502, h)
    r.pipe(res)
  })
  up.on('error', () => res.headersSent ? res.destroy() : page(res, 502, `${l.label} is not running`, 'The preview is stopped right now. Try again in a bit.'))
  req.pipe(up)
})

pub.on('upgrade', (req, sock, head) => {
  const l = linkFor(req)
  if (!l) return sock.destroy()
  const [host, port] = l.target.split(':')
  const up = net.connect(+port, host, () => {
    const h = headersFor(req, l)
    h.connection = 'Upgrade'
    up.write(`${req.method} ${req.url} HTTP/1.1\r\n` + Object.entries(h).map(([k, v]) => `${k}: ${v}`).join('\r\n') + '\r\n\r\n')
    if (head?.length) up.write(head)
    up.pipe(sock); sock.pipe(up)
  })
  up.on('error', () => sock.destroy())
  sock.on('error', () => up.destroy())
})
pub.listen(PUBLIC_PORT, '127.0.0.1')

// --- control (dashboard app only) --------------------------------------------
function funnel() {
  return new Promise(ok => execFile('tailscale', ['funnel', 'status', '--json'], { timeout: 5000 }, (e, out) => {
    try {
      const j = JSON.parse(out || '{}')
      const on = Object.entries(j.AllowFunnel || {}).some(([k, v]) => v && k.endsWith(':8443'))
      ok({ on, host: Object.keys(j.Web || {}).find(k => k.endsWith(':8443'))?.replace(/:8443$/, '') || null })
    } catch { ok({ on: false, host: null }) }
  }))
}

const body = req => new Promise((ok, no) => {
  let s = ''
  req.on('data', d => { s += d; if (s.length > 1e5) req.destroy() })
  req.on('end', () => { try { ok(s ? JSON.parse(s) : {}) } catch (e) { no(e) } })
})
const send = (res, code, o) => { res.writeHead(code, { 'content-type': 'application/json' }); res.end(JSON.stringify(o)) }

http.createServer(async (req, res) => {
  try {
    if (req.method === 'GET' && req.url === '/links') {
      const links = db.links.map(l => ({ ...l, status: status(l), visitors: Object.values(db.sessions).filter(s => s.link === l.id && s.expires > Date.now()).length }))
      return send(res, 200, { links: links.reverse(), funnel: await funnel() })
    }
    if (req.method !== 'POST') return send(res, 404, { error: 'not found' })
    const b = await body(req)
    if (req.url === '/links') {
      if (!TARGET_RE.test(String(b.target))) return send(res, 400, { error: 'bad target' })
      const ttl = Number(b.ttl) || 0
      const l = {
        id: crypto.randomBytes(6).toString('hex'), token: crypto.randomBytes(24).toString('base64url'),
        label: String(b.label || 'project').slice(0, 80), project: b.project ?? null, target: b.target,
        once: !!b.once, expires: ttl > 0 ? Date.now() + ttl * 1000 : null, created: Date.now(), uses: 0, revoked: false,
      }
      db.links.push(l); save()
      return send(res, 200, l)
    }
    const l = db.links.find(x => x.id === b.id)
    if (!l) return send(res, 404, { error: 'no such link' })
    if (req.url === '/revoke') {
      l.revoked = true
      for (const [sid, s] of Object.entries(db.sessions)) if (s.link === l.id) delete db.sessions[sid]
    } else if (req.url === '/delete') {
      db.links = db.links.filter(x => x !== l)
      for (const [sid, s] of Object.entries(db.sessions)) if (s.link === l.id) delete db.sessions[sid]
    } else return send(res, 404, { error: 'not found' })
    save()
    send(res, 200, { ok: true })
  } catch (e) { send(res, 400, { error: String(e?.message || e) }) }
}).listen(CTL_PORT, '127.0.0.1')
