/** Imagine's agent routes, nothing else: every argument is rebuilt and checked before it reaches the agent
 *  (writes are same-origin like every /api POST; the add-on's `roles:` gate who may call it) */
const STYLES = ['photo', 'anime', 'pixel', 'logo']
const SIZES = ['square', 'portrait', 'landscape', 'phone']
const ID = /^[a-f0-9]{10}$/
const UPLOAD = /^up-[a-f0-9]{10}\.png$/
const UPLOAD_B64 = Math.ceil(10 * 1024 * 1024 / 3) * 4 // 10 MB decoded, the agent's cap, as base64 (the chat's file upload sends base64 JSON too)
const KEYS = ['subject', 'setting', 'composition', 'lighting', 'colors', 'mood']

/** the edit JSON, rebuilt field by field: known keys only, strings capped (200; details 6 x 120) */
function editJson(v: any) {
  const o: any = v && typeof v === 'object' ? v : {}
  const out: Record<string, any> = {}
  for (const k of KEYS) out[k] = typeof o[k] === 'string' ? o[k].trim().slice(0, 200) : ''
  out.details = (Array.isArray(o.details) ? o.details : []).filter((x: any) => typeof x === 'string').map((x: string) => x.trim().slice(0, 120)).filter(Boolean).slice(0, 6)
  return out
}

const GENDERS = ['girl', 'boy', 'other']
const VERDICTS = ['good', 'bad', 'clear']
const LOOKS = ['hair', 'eyes', 'build', 'outfit', 'extras']
const bad = (m: string) => createError({ statusCode: 400, statusMessage: m })

/** the character form, rebuilt field by field like the agent does: age is a whole number from 18 up (a string or a fraction is refused), texts capped, never silently cut */
function charBody(b: any) {
  const text = (k: string, cap: number, req = false) => {
    const v = b?.[k]
    if (v !== undefined && v !== null && typeof v !== 'string') throw bad(`${k} must be text`)
    const t = (v ?? '').trim()
    if (t.length > cap) throw bad(`${k} is too long (${cap} characters at most)`)
    if (req && !t) throw bad('give the character a name')
    return t
  }
  const name = text('name', 60, true)
  if (!GENDERS.includes(b?.gender)) throw bad('unknown gender')
  if (typeof b?.age !== 'number' || !Number.isInteger(b.age) || b.age < 18 || b.age > 999) throw bad('age must be a whole number, 18 or older')
  if (b?.adult !== undefined && typeof b.adult !== 'boolean') throw bad('adult must be on or off')
  const out: Record<string, any> = { name, gender: b.gender, age: b.age, note: text('note', 300), adult: b.adult === true }
  for (const k of LOOKS) out[k] = text(k, 120)
  if (b?.id !== undefined && b.id !== null && b.id !== '') {
    if (!ID.test(String(b.id))) throw bad('bad character id')
    out.id = b.id
  }
  return out
}

export default defineEventHandler(async (event) => {
  const path = String(getRouterParam(event, 'path') ?? '')
  if (event.method === 'GET' && path === 'state') return agent(event, '/imagine/state')
  if (event.method === 'GET' && path === 'characters') return agent(event, '/imagine/characters')
  if (event.method !== 'POST') throw createError({ statusCode: 405, statusMessage: 'method not allowed' })
  const b: any = await readBody(event)
  if (path === 'submit') {
    const prompt = String(b?.prompt ?? '').trim().slice(0, 1000)
    const count = Number(b?.count)
    if (!prompt) throw createError({ statusCode: 400, statusMessage: 'write a prompt first' })
    if (!STYLES.includes(b?.style) || !SIZES.includes(b?.size) || !(count >= 1 && count <= 4)) throw createError({ statusCode: 400, statusMessage: 'bad request' })
    if (b?.adult !== undefined && typeof b.adult !== 'boolean') throw createError({ statusCode: 400, statusMessage: 'bad request' })
    if (b?.character !== undefined && b.character !== null && !ID.test(String(b.character))) throw createError({ statusCode: 400, statusMessage: 'bad character id' })
    if (b?.same_look !== undefined && typeof b.same_look !== 'boolean') throw createError({ statusCode: 400, statusMessage: 'bad request' })
    const chr = b?.character ? { character: b.character, same_look: b.same_look === true } : {}
    return agent(event, '/imagine/submit', { method: 'POST', body: { prompt, style: b.style, size: b.size, draft: !!b.draft, count: Math.floor(count), adult: b.adult === true, ...chr } })
  }
  if (path === 'character/save') return agent(event, '/imagine/character/save', { method: 'POST', body: charBody(b) })
  if (path === 'character/delete' || path === 'character/looks' || path === 'character/batch' || path === 'character/cleanup' || path === 'character/reference' || path === 'character/rate') {
    const id = String(b?.id ?? '')
    if (!ID.test(id)) throw bad('bad character id')
    if (path !== 'character/reference' && path !== 'character/rate') return agent(event, `/imagine/${path}`, { method: 'POST', body: { id } })
    const job = String(b?.job ?? '')
    const n = Number(b?.n)
    if (!ID.test(job) || !(n >= 1 && n <= 4)) throw bad('bad image')
    if (path === 'character/rate') {
      if (!VERDICTS.includes(b?.verdict)) throw bad('verdict must be good, bad or clear')
      return agent(event, '/imagine/character/rate', { method: 'POST', body: { id, job, n: Math.floor(n), verdict: b.verdict } })
    }
    return agent(event, '/imagine/character/reference', { method: 'POST', body: { id, job, n: Math.floor(n) } })
  }
  if (path === 'character/upload' || path === 'character/upload/delete') {
    const id = String(b?.id ?? '')
    if (!ID.test(id)) throw bad('bad character id')
    if (path === 'character/upload/delete') {
      const file = String(b?.file ?? '')
      if (!UPLOAD.test(file)) throw bad('bad file name')
      return agent(event, '/imagine/character/upload/delete', { method: 'POST', body: { id, file } })
    }
    if (b?.ack !== true) throw bad('confirm these are your own pictures of an original character')
    const data = typeof b?.data === 'string' ? b.data : ''
    if (!data || data.length > UPLOAD_B64 || !/^[A-Za-z0-9+/]+={0,2}$/.test(data)) throw bad('the file is missing or over 10 MB')
    const name = typeof b?.name === 'string' ? b.name.slice(0, 200) : ''
    return agent(event, '/imagine/character/upload', { method: 'POST', body: { id, name, data, ack: true } })
  }
  if (path === 'json' || path === 'regenerate') {
    const job = String(b?.job ?? '')
    const n = Number(b?.n)
    if (!ID.test(job) || !(n >= 1 && n <= 4)) throw createError({ statusCode: 400, statusMessage: 'bad image' })
    const base = { job, n: Math.floor(n) }
    if (path === 'json') return agent(event, '/imagine/json', { method: 'POST', body: base })
    if (b?.adult !== undefined && typeof b.adult !== 'boolean') throw createError({ statusCode: 400, statusMessage: 'bad request' })
    const adult = typeof b?.adult === 'boolean' ? { adult: b.adult } : {} // absent = keep the source's
    return agent(event, '/imagine/regenerate', { method: 'POST', body: { ...base, json: editJson(b?.json), keep_seed: !!b?.keep_seed, ...adult } })
  }
  if (path === 'cancel' || path === 'dismiss' || path === 'delete') {
    const key = path === 'delete' ? 'job' : 'id'
    const id = String(b?.[key] ?? '')
    if (!ID.test(id)) throw createError({ statusCode: 400, statusMessage: 'bad id' })
    if (path === 'cancel' || path === 'dismiss') return agent(event, `/imagine/${path}`, { method: 'POST', body: { id } })
    const n = Number(b?.n)
    if (!(n >= 1 && n <= 4)) throw createError({ statusCode: 400, statusMessage: 'bad image' })
    return agent(event, '/imagine/delete', { method: 'POST', body: { job: id, n: Math.floor(n) } })
  }
  throw createError({ statusCode: 404, statusMessage: 'not found' })
})
