/** Imagine's state and calls. Polls every 3 s while a job is queued, running or paused, every 15 s otherwise, and not at all
 *  while the tab is hidden. */
export interface ImagineJob { id: string, prompt: string, style: string, size: string, draft: boolean, adult?: boolean, count: number, status: string, done_n: number, error: string, created: number, phase?: string }
export interface ImagineImage { job: string, n: number, date: string, file: string, ts: number, prompt: string, style: string, size: string, draft: boolean, adult: boolean, parent: { job: string, n: number } | null, character: string | null, scene: string }
export interface ImagineEdit { subject: string, setting: string, composition: string, lighting: string, colors: string, mood: string, details: string[] }
export interface ImagineCharacter {
  id: string, name: string, gender: 'girl' | 'boy' | 'other', age: number, hair: string, eyes: string, build: string, outfit: string, extras: string, note: string, adult: boolean,
  reference: { job: string, n: number, seed: number | null, file: string } | null, created: number, looks: ImagineImage[]
  // stage A: set = the reference first, then the approved copies; unrated = character pictures not yet rated; rejected = marked bad and still in the gallery
  set: { job?: string, n?: number, file: string, prompt: string, reference: boolean, source?: 'upload', name?: string }[], unrated: ImagineImage[], rejected: ImagineImage[], rejected_n: number
  target: { min: number, max: number, have: number, limit: number }
}
export type ImagineCharacterForm = Omit<ImagineCharacter, 'id' | 'reference' | 'created' | 'looks' | 'set' | 'unrated' | 'rejected' | 'rejected_n' | 'target'> & { id?: string }
export type ImagineVerdict = 'good' | 'bad' | 'clear'
export interface ImagineState { queue: ImagineJob[], gallery: ImagineImage[], games: boolean, ready: boolean, ai_up?: boolean, message: string, voice_paused?: boolean }

export function useImagine() {
  const { t } = useI18n()
  const { toast } = useToast()
  const data = ref<ImagineState | null>(null)
  const failed = ref('')
  const chars = ref<ImagineCharacter[] | null>(null)
  const charsFailed = ref('')
  const live = computed(() => (data.value?.queue ?? []).filter(j => ['queued', 'running', 'paused'].includes(j.status)))
  const active = computed(() => live.value.length > 0)

  async function refresh() {
    try { data.value = await $fetch<ImagineState>('/api/imagine/state'); failed.value = '' }
    catch (e: any) { failed.value = e?.data?.statusMessage || e?.message || t('imagine.loadFailed') }
  }
  async function refreshChars() {
    try { chars.value = (await $fetch<{ characters: ImagineCharacter[] }>('/api/imagine/characters')).characters; charsFailed.value = '' }
    catch (e: any) { charsFailed.value = e?.data?.statusMessage || e?.message || t('imagine.loadFailed') }
  }
  const err = (e: any) => toast(e?.data?.statusMessage || e?.message || t('imagine.failed'), { tone: 'bad' })
  const call = (path: string, body: Record<string, any>) => $fetch<any>(`/api/imagine/${path}`, { method: 'POST', body })

  async function submit(b: { prompt: string, style: string, size: string, draft: boolean, count: number, adult: boolean, character?: string, same_look?: boolean }) {
    try { await call('submit', b); await refresh(); return true } catch (e: any) { err(e); await refresh(); return false }
  }
  async function cancel(id: string) { try { await call('cancel', { id }); await refresh() } catch (e: any) { err(e) } }
  async function dismiss(id: string) { try { await call('dismiss', { id }); await refresh() } catch (e: any) { err(e) } }
  async function remove(img: ImagineImage) {
    try { await call('delete', { job: img.job, n: img.n }); await refresh(); return true } catch (e: any) { err(e); return false }
  }

  // edit flow: the fields come from the one qwen split of the original prompt; errors are shown by the caller (a toast would hide them behind the viewer), so editJson throws
  const editJson = (img: ImagineImage) => call('json', { job: img.job, n: img.n }) as Promise<{ json: ImagineEdit }>
  async function regenerate(img: ImagineImage, json: ImagineEdit, keep_seed: boolean, adult: boolean) {
    try { await call('regenerate', { job: img.job, n: img.n, json, keep_seed, adult }); await refresh(); return true } catch (e: any) { err(e); await refresh(); return false }
  }

  // characters: the errors of save / looks / reference are shown by the editor itself (they throw), the rest toast
  async function saveChar(f: ImagineCharacterForm) { const r = await call('character/save', f); await refreshChars(); return r.character as ImagineCharacter }
  async function deleteChar(id: string) { try { await call('character/delete', { id }); await refreshChars(); return true } catch (e: any) { err(e); return false } }
  async function makeLooks(id: string) { await call('character/looks', { id }); await Promise.all([refresh(), refreshChars()]) }
  async function setReference(id: string, img: ImagineImage) { await call('character/reference', { id, job: img.job, n: img.n }); await refreshChars() }

  // stage A: errors are shown by the caller (they throw)
  async function makeBatch(id: string) { await call('character/batch', { id }); await Promise.all([refresh(), refreshChars()]) }
  async function rate(id: string, job: string, n: number, verdict: ImagineVerdict) { await call('character/rate', { id, job, n, verdict }); await refreshChars() }
  // uploads: the file goes up as base64 JSON, one at a time by the caller (errors throw)
  async function uploadPic(id: string, name: string, data: string) { await call('character/upload', { id, name, data, ack: true }); await refreshChars() }
  async function removePic(id: string, file: string) { await call('character/upload/delete', { id, file }); await refreshChars() }
  async function cleanup(id: string) { await call('character/cleanup', { id }); await Promise.all([refresh(), refreshChars()]) }

  let timer: any
  const tick = async () => {
    if (!document.hidden) await Promise.all([refresh(), refreshChars()])
    timer = setTimeout(tick, active.value ? 3000 : 15000)
  }
  const onVis = () => { if (!document.hidden) { clearTimeout(timer); tick() } }
  onMounted(() => { tick(); document.addEventListener('visibilitychange', onVis) })
  onBeforeUnmount(() => { clearTimeout(timer); document.removeEventListener('visibilitychange', onVis) })

  return { data, failed, chars, charsFailed, refreshChars, saveChar, deleteChar, makeLooks, setReference, makeBatch, rate, uploadPic, removePic, cleanup, live, active, refresh, submit, cancel, dismiss, remove, editJson, regenerate }
}
