/** use a design: { pick: 'p:<built-in>' | 'd:<id>', device? } — with a device only that kind of device switches,
 *  and { pick: 'follow', device } puts it back on the account's design */
export default defineEventHandler(async (event) => {
  const uid = uidOf(event)
  const b = await readBody(event)
  const device = okDevice(b?.device)
  setPick(uid, String(b?.pick ?? ''), device)
  return { pick: pickOf(uid, device), look: activeLook(uid, device) }
})
