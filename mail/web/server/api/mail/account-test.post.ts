// logs in over IMAP and SMTP, sends nothing; by saved id or by the unsaved form fields
export default defineEventHandler(async (event) => {
  const b = await readBody(event)
  const s = (v: any, n: number) => String(v ?? '').slice(0, n)
  return agent(event, '/mail/account/test', { method: 'POST', timeout: 40_000, body: {
    id: s(b?.id, 24), label: s(b?.label, 80), email: s(b?.email, 320), username: s(b?.username, 200), password: s(b?.password, 500),
    provider: s(b?.provider, 12), imap_host: s(b?.imap_host, 253), imap_port: s(b?.imap_port, 6), smtp_host: s(b?.smtp_host, 253), smtp_port: s(b?.smtp_port, 6),
  } })
})
