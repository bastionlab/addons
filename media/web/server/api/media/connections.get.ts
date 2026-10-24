/** Media's connection for /settings: the VPN the download stack sits behind */
export default defineEventHandler(async (event) => {
  const v = (await mediaData(event) as any)?.vpn
  if (!v) return [{ id: 'vpn', name: 'VPN (gluetun)', ok: false, detail: 'no answer from the download stack' }]
  const ok = v.up && v.killSwitch && !v.leaking
  return [{ id: 'vpn', name: 'VPN (gluetun)', ok, warn: ok && !v.portOk,
    detail: !v.up ? 'tunnel down' : v.leaking ? 'LEAKING your home IP' : !v.killSwitch ? 'kill switch off'
      : `${v.city ?? v.country ?? 'up'}${v.portOk ? '' : ' · forwarded port not open'}`,
    fix: 'VPN credentials live in the dl CT (gluetun); this only watches it' }]
})
