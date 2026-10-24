/** Money's connections for /settings: the Enable Banking app, each bank consent (≤ 180 days), Trade Republic */
export default defineEventHandler(async (event) => {
  const d: any = await money(event, '/overview')
  const s = d.setup ?? {}
  const out: any[] = [{ id: 'eb', name: 'Enable Banking app', ok: !!s.eb, detail: s.eb ? `app ${s.eb_app_id}` : 'not set up' }]
  for (const l of d.links ?? []) {
    const days = Math.round((new Date(l.valid_until).getTime() - Date.now()) / 86400000)
    out.push({ id: `bank-${l.session_id}`, name: `${l.aspsp} consent`, ok: days > 0, warn: days > 0 && days <= 14,
      detail: days > 0 ? `${days} days left` : 'expired — renew', expires: l.valid_until })
  }
  const tr = (d.accounts ?? []).find((a: any) => a.source === 'tr')
  if (s.tr || tr) {
    const st = s.tr_login?.state
    out.push({ id: 'tr', name: 'Trade Republic login', ok: !tr?.error && st !== 'need_code', warn: !!tr?.error || st === 'waiting_app',
      detail: st === 'need_code' ? 'enter the code' : st === 'waiting_app' ? 'confirm in the TR app' : tr?.error ? 'log in again (TR ends logins after 24 h)' : 'logged in' })
  }
  return out
})
