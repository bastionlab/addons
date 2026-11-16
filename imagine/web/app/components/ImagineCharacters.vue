<script setup lang="ts">
import type { ImagineCharacter, ImagineCharacterForm, ImagineImage, ImagineVerdict } from '../composables/useImagine'

/** The Characters tab: a list of fictional adult characters and an editor. Everything is saved by hand; no AI writes the fields. */
const props = defineProps<{
  chars: ImagineCharacter[] | null, failed: string, blocked: string
  save: (f: ImagineCharacterForm) => Promise<ImagineCharacter>, remove: (id: string) => Promise<boolean>, looks: (id: string) => Promise<void>
  batch: (id: string) => Promise<void>, rate: (id: string, job: string, n: number, v: ImagineVerdict) => Promise<void>, cleanup: (id: string) => Promise<void>
  upload: (id: string, name: string, data: string) => Promise<void>, removePic: (id: string, file: string) => Promise<void>
}>()
const emit = defineEmits<{ view: [id: string, index: number] }>()
const { t } = useI18n()
const { toast } = useToast()
const { armed, arm } = useArm()

const GENDERS = ['girl', 'boy', 'other'] as const
const LOOK_FIELDS = ['hair', 'eyes', 'build', 'outfit', 'extras'] as const
const blank = () => ({ id: '', name: '', gender: 'girl' as ImagineCharacter['gender'], ageText: '', hair: '', eyes: '', build: '', outfit: '', extras: '', note: '', adult: false })
const form = reactive(blank())
const sel = ref('') // '' = nothing open, 'new' = an unsaved character, else the id
const touched = ref(false)
const saving = ref(false)
const making = ref(false)
const err = ref('')
const editor = ref<HTMLElement | null>(null)

const cur = computed(() => props.chars?.find(c => c.id === sel.value) ?? null)
const apiErr = (e: any) => e?.data?.statusMessage || e?.message || t('imagine.failed')
const ageOk = computed(() => /^\d{1,3}$/.test(form.ageText.trim()) && Number(form.ageText) >= 18)
const ageErr = computed(() => (touched.value || form.ageText) && !ageOk.value ? t('imagine.chars.ageErr') : '')
const nameErr = computed(() => touched.value && !form.name.trim() ? t('imagine.chars.nameErr') : '')
const valid = computed(() => ageOk.value && !!form.name.trim())
const body = (): ImagineCharacterForm => ({
  ...(form.id ? { id: form.id } : {}), name: form.name.trim(), gender: form.gender, age: Number(form.ageText), adult: form.adult, note: form.note.trim(),
  hair: form.hair.trim(), eyes: form.eyes.trim(), build: form.build.trim(), outfit: form.outfit.trim(), extras: form.extras.trim(),
})
const dirty = computed(() => {
  const c = cur.value
  if (!c) return true
  const b = body()
  return (['name', 'gender', 'age', 'adult', 'note', ...LOOK_FIELDS] as const).some(k => (b as any)[k] !== (c as any)[k])
})
const looksWhy = computed(() => dirty.value ? t('imagine.chars.saveFirst') : props.blocked)

function fill(c: ImagineCharacter | null) {
  Object.assign(form, blank(), c ? { id: c.id, name: c.name, gender: c.gender, ageText: String(c.age), adult: c.adult, note: c.note, ...Object.fromEntries(LOOK_FIELDS.map(k => [k, c[k]])) } : {})
  touched.value = false
  err.value = ''
  nextTick(() => editor.value?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }))
}
function open(c: ImagineCharacter) { sel.value = c.id; fill(c) }
watch(sel, () => { own.value = false; queue.value = queue.value.filter(q => q.state !== 'err') })
function add() { sel.value = 'new'; fill(null) }

async function doSave() {
  touched.value = true
  if (!valid.value || saving.value) return
  saving.value = true
  err.value = ''
  try {
    const c = await props.save(body())
    sel.value = c.id
    form.id = c.id
    toast(t('imagine.chars.saved'), { tone: 'ok' })
  } catch (e: any) { err.value = apiErr(e) }
  saving.value = false
}
async function doDelete() {
  if (!cur.value || !arm(`char-${cur.value.id}`)) return
  if (await props.remove(cur.value.id)) { sel.value = ''; toast(t('imagine.deleted'), { tone: 'ok' }) }
}
async function doLooks() {
  if (!cur.value || making.value || looksWhy.value) return
  making.value = true
  err.value = ''
  try { await props.looks(cur.value.id); toast(t('imagine.submitted'), { tone: 'ok' }) } catch (e: any) { err.value = apiErr(e) }
  making.value = false
}
// stage A: reference -> rated batches -> approved set
const batching = ref(false)
const rating = ref('')
const showRej = ref(false)
const lookBox = ref<HTMLElement | null>(null)
const batchWhy = computed(() => dirty.value ? t('imagine.chars.saveFirst') : !cur.value?.reference ? t('imagine.chars.noReference') : props.blocked)
const imgKey = (i: { job?: string, n?: number, file?: string }) => i.job ? `${i.job}-${i.n}` : (i.file ?? '')
function viewAt(i: { job?: string, n?: number }) {
  const at = i.job ? cur.value?.looks.findIndex(l => l.job === i.job && l.n === i.n) ?? -1 : -1
  if (cur.value && at >= 0) emit('view', cur.value.id, at)
}
async function doBatch() {
  if (!cur.value || batching.value || batchWhy.value) return
  batching.value = true
  err.value = ''
  try { await props.batch(cur.value.id); toast(t('imagine.chars.batchQueued'), { tone: 'ok' }) } catch (e: any) { err.value = apiErr(e) }
  batching.value = false
}
async function doRate(i: { job: string, n: number }, v: ImagineVerdict) {
  if (!cur.value || rating.value) return
  rating.value = imgKey(i)
  try { await props.rate(cur.value.id, i.job, i.n, v) } catch (e: any) { toast(apiErr(e), { tone: 'bad' }) }
  rating.value = ''
}
async function doCleanup() {
  if (!cur.value || !arm(`clean-${cur.value.id}`)) return
  try { await props.cleanup(cur.value.id); showRej.value = false; toast(t('imagine.chars.cleanupDone'), { tone: 'ok' }) } catch (e: any) { toast(apiErr(e), { tone: 'bad' }) }
}
// own pictures: the tick is per visit (not stored); files go up one at a time as base64 JSON, like the chat's file upload
const UP_MIB = 10
const own = ref(false)
const picker = ref<HTMLInputElement | null>(null)
const queue = ref<{ key: number, name: string, state: 'wait' | 'up' | 'err', msg: string }[]>([])
const pumping = ref(false)
let qn = 0
const uploading = computed(() => queue.value.some(q => q.state === 'wait' || q.state === 'up'))
const upErrs = computed(() => queue.value.filter(q => q.state === 'err'))
const b64 = (f: File) => new Promise<string>((ok, no) => {
  const r = new FileReader()
  r.onload = () => ok(String(r.result).split(',')[1] ?? '')
  r.onerror = () => no(new Error(t('imagine.chars.upRead')))
  r.readAsDataURL(f)
})
async function pump(id: string) {
  if (pumping.value) return
  pumping.value = true
  for (;;) {
    const q = queue.value.find(x => x.state === 'wait')
    const f = q && files.get(q.key)
    if (!q || !f) break
    q.state = 'up'
    try {
      if (f.size > UP_MIB * 1024 * 1024) throw new Error(t('imagine.chars.upBig', { mb: UP_MIB }))
      await props.upload(id, f.name, await b64(f))
      queue.value = queue.value.filter(x => x !== q)
    } catch (e: any) { q.state = 'err'; q.msg = apiErr(e) }
    files.delete(q.key)
  }
  pumping.value = false
}
const files = new Map<number, File>()
function pick(ev: Event) {
  const el = ev.target as HTMLInputElement
  const c = cur.value
  if (!c || !own.value) { el.value = ''; return }
  queue.value = queue.value.filter(q => q.state !== 'err')
  for (const f of Array.from(el.files ?? [])) { const key = ++qn; files.set(key, f); queue.value.push({ key, name: f.name, state: 'wait', msg: '' }) }
  el.value = ''
  pump(c.id)
}
async function doRemovePic(file: string) {
  if (!cur.value || !arm(`up-${file}`)) return
  try { await props.removePic(cur.value.id, file) } catch (e: any) { toast(apiErr(e), { tone: 'bad' }) }
}
const upFile = (p: string) => p.split('/').pop() ?? p
const toLooks = () => lookBox.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
const refUrl = (c: ImagineCharacter) => c.reference ? `${imagineRaw(c.reference.file)}&v=${c.reference.job}${c.reference.n}` : ''
// a deleted character (another device) closes the editor
watch(() => props.chars, (l) => { if (l && sel.value && sel.value !== 'new' && !l.some(c => c.id === sel.value)) sel.value = '' })
</script>

<template>
  <div class="chars">
    <div v-if="failed && !chars" class="errbox">{{ failed }}</div>
    <Skeleton v-else-if="!chars" kind="cards" :n="4" />
    <div v-else class="cgrid">
      <div class="clist">
        <button type="button" class="btn primary new" @click="add"><Icon name="plus" :size="16" /> {{ $t('imagine.chars.new') }}</button>
        <p v-if="!chars.length" class="empty-state">{{ $t('imagine.chars.empty') }}</p>
        <ul v-else class="cards">
          <li v-for="c in chars" :key="c.id">
            <button type="button" class="ccard" :class="{ on: sel === c.id }" :aria-pressed="sel === c.id" @click="open(c)">
              <span class="cimg"><img v-if="c.reference" :src="refUrl(c)" :alt="c.name" loading="lazy" decoding="async"><Icon v-else name="users" :size="20" /></span>
              <span class="ctxt"><span class="cn">{{ c.name }}</span><span class="small muted">{{ $t('imagine.chars.ageOf', { age: c.age }) }}</span></span>
            </button>
          </li>
        </ul>
      </div>

      <div ref="editor" class="ed">
        <Panel v-if="sel" :title="cur ? cur.name : $t('imagine.chars.new')" id="imagine-character">
          <form class="form" novalidate @submit.prevent="doSave">
            <label class="fld"><span class="lab">{{ $t('imagine.chars.name') }}</span><input v-model="form.name" type="text" maxlength="60" autocomplete="off" :aria-invalid="!!nameErr"><span v-if="nameErr" class="small bad">{{ nameErr }}</span></label>
            <div class="two">
              <div class="fld"><span class="lab">{{ $t('imagine.chars.gender') }}</span><div class="seg"><button v-for="g in GENDERS" :key="g" type="button" :class="{ on: form.gender === g }" @click="form.gender = g">{{ $t(`imagine.chars.genders.${g}`) }}</button></div></div>
              <label class="fld"><span class="lab">{{ $t('imagine.chars.age') }}</span><input v-model="form.ageText" type="text" inputmode="numeric" maxlength="3" autocomplete="off" :aria-invalid="!!ageErr" :aria-describedby="ageErr ? 'imc-age' : undefined"><span v-if="ageErr" id="imc-age" class="small bad">{{ ageErr }}</span></label>
            </div>
            <div class="two">
              <label v-for="k in LOOK_FIELDS" :key="k" class="fld"><span class="lab">{{ $t(`imagine.chars.${k}`) }}</span><input v-model="form[k]" type="text" maxlength="120" autocomplete="off"></label>
            </div>
            <label class="fld"><span class="lab">{{ $t('imagine.chars.note') }}</span><textarea v-model="form.note" rows="3" maxlength="300" /></label>
            <div class="adult">
              <div class="at"><span class="lab">{{ $t('imagine.adult') }}</span><button type="button" class="sw" :class="{ on: form.adult }" role="switch" :aria-checked="form.adult" :aria-label="$t('imagine.adult')" @click="form.adult = !form.adult"><i /></button></div>
              <p class="small muted ah">{{ $t('imagine.chars.adultHint') }}</p>
            </div>
            <div v-if="err" class="errbox small">{{ err }}</div>
            <div class="acts">
              <button type="submit" class="btn primary" :disabled="saving || !valid"><Icon name="check" :size="16" /> {{ $t('imagine.chars.save') }}</button>
              <button v-if="cur" type="button" class="btn danger" :class="{ sure: armed === `char-${cur.id}` }" @click="doDelete"><Icon name="trash-2" :size="16" /> {{ armed === `char-${cur.id}` ? $t('imagine.sure') : $t('imagine.delete') }}</button>
            </div>
          </form>

          <div v-if="cur" class="stage">
          <section class="blk" :style="{ order: 1 }" :aria-label="$t('imagine.chars.reference')">
            <div class="lh">
              <h3 class="sec">{{ $t('imagine.chars.reference') }}</h3>
              <button v-if="cur.reference" type="button" class="btn sm" @click="toLooks">{{ $t('imagine.chars.change') }}</button>
            </div>
            <button v-if="cur.reference" type="button" class="ref" :aria-label="$t('imagine.chars.reference')" @click="viewAt(cur.reference)">
              <img :src="refUrl(cur)" :alt="cur.name" decoding="async">
            </button>
            <p v-else class="small muted why">{{ $t('imagine.chars.noReference') }}</p>
          </section>

          <section class="blk" :style="{ order: 2 }">
            <div class="lh">
              <button type="button" class="btn primary" :disabled="batching || !!batchWhy" @click="doBatch"><Icon name="sparkles" :size="16" /> {{ $t('imagine.chars.makeMore') }}</button>
            </div>
            <p v-if="batchWhy" class="small muted why">{{ batchWhy }}</p>
          </section>

          <section class="blk" :style="{ order: 3 }" :aria-label="$t('imagine.chars.toRate')">
            <div class="lh"><h3 class="sec">{{ $t('imagine.chars.toRate') }}</h3><span v-if="cur.unrated.length" class="pill">{{ cur.unrated.length }}</span></div>
            <p v-if="!cur.unrated.length" class="small muted">{{ $t('imagine.chars.nothingToRate') }}</p>
            <div v-else class="rgrid">
              <figure v-for="i in cur.unrated" :key="imgKey(i)" class="rcard">
                <button type="button" class="rimg" :aria-label="i.prompt" @click="viewAt(i)"><img :src="imagineRaw(i.file)" :alt="i.prompt" loading="lazy" decoding="async"></button>
                <div class="rbtns">
                  <button type="button" class="btn rate" :disabled="!!rating" @click="doRate(i, 'good')"><Icon name="check" :size="18" /> {{ $t('imagine.chars.good') }}</button>
                  <button type="button" class="btn rate" :disabled="!!rating" @click="doRate(i, 'bad')"><Icon name="x" :size="18" /> {{ $t('imagine.chars.bad') }}</button>
                </div>
              </figure>
            </div>
          </section>

          <section class="blk" :style="{ order: 4 }" :aria-label="$t('imagine.chars.set')">
            <div class="lh"><h3 class="sec">{{ $t('imagine.chars.set') }}</h3><span class="small muted num">{{ $t('imagine.chars.setProgress', { have: cur.target.have, max: cur.target.max }) }}</span></div>
            <div class="bar" role="presentation"><i :style="{ width: Math.min(100, cur.target.have / cur.target.max * 100) + '%' }" /></div>
            <label class="own small"><input v-model="own" type="checkbox"><span>{{ $t('imagine.chars.ownOnly') }}</span></label>
            <div class="lh">
              <input ref="picker" class="hid" type="file" multiple accept="image/png,image/jpeg,image/webp" tabindex="-1" aria-hidden="true" @change="pick">
              <button type="button" class="btn" :disabled="!own || cur.target.have >= cur.target.limit" @click="picker?.click()"><Icon name="plus" :size="16" /> {{ $t('imagine.chars.addPics') }}</button>
            </div>
            <ul v-if="queue.length" class="upq small" aria-live="polite">
              <li v-for="q in queue" :key="q.key" :class="{ bad: q.state === 'err' }"><span class="un">{{ q.name }}</span><span class="muted">{{ q.state === 'up' ? $t('imagine.chars.upSending') : q.state === 'wait' ? $t('imagine.chars.upWaiting') : '' }}</span></li>
            </ul>
            <div v-if="upErrs.length" class="errbox small"><p v-for="q in upErrs" :key="q.key" class="eline"><b>{{ q.name }}</b>: {{ q.msg }}</p></div>
            <div v-if="cur.set.length" class="sgrid">
              <figure v-for="i in cur.set" :key="imgKey(i)" class="scard">
                <a v-if="i.source === 'upload'" class="look" :href="imagineRaw(i.file)" target="_blank" rel="noopener" :aria-label="i.name || $t('imagine.chars.upload')"><img :src="imagineRaw(i.file)" :alt="i.name || ''" loading="lazy" decoding="async"></a>
                <button v-else type="button" class="look" :aria-label="i.prompt || $t('imagine.chars.reference')" @click="viewAt(i)"><img :src="imagineRaw(i.file)" :alt="i.prompt" loading="lazy" decoding="async"></button>
                <span v-if="i.reference" class="tag" aria-hidden="true"><Icon name="star" :size="12" /></span>
                <template v-else-if="i.source === 'upload'">
                  <span class="pill accent up">{{ $t('imagine.chars.upload') }}</span>
                  <button type="button" class="btn ghost sm icon rm" :class="{ sure: armed === `up-${upFile(i.file)}` }" :aria-label="$t('imagine.chars.setRemove')" @click="doRemovePic(upFile(i.file))"><template v-if="armed === `up-${upFile(i.file)}`">{{ $t('imagine.sure') }}</template><Icon v-else name="x" :size="14" /></button>
                </template>
                <button v-else type="button" class="btn ghost sm icon rm" :disabled="!!rating" :aria-label="$t('imagine.chars.setRemove')" @click="doRate(i, 'clear')"><Icon name="x" :size="14" /></button>
              </figure>
            </div>
          </section>

          <section v-if="cur.rejected_n" class="blk" :style="{ order: 5 }">
            <div class="lh">
              <button type="button" class="lnk head" :aria-expanded="showRej" @click="showRej = !showRej"><Icon :name="showRej ? 'chevron-up' : 'chevron-down'" :size="16" /> {{ $t('imagine.chars.rejected', { n: cur.rejected_n }) }}</button>
              <button type="button" class="btn danger sm" :class="{ sure: armed === `clean-${cur.id}` }" @click="doCleanup"><Icon name="trash-2" :size="16" /> {{ armed === `clean-${cur.id}` ? $t('imagine.sure') : $t('imagine.chars.cleanup') }}</button>
            </div>
            <div v-if="showRej" class="sgrid">
              <figure v-for="i in cur.rejected" :key="imgKey(i)" class="scard">
                <button type="button" class="look dim" :aria-label="i.prompt" @click="viewAt(i)"><img :src="imagineRaw(i.file)" :alt="i.prompt" loading="lazy" decoding="async"></button>
                <button type="button" class="btn ghost sm rm2" :disabled="!!rating" @click="doRate(i, 'clear')">{{ $t('imagine.chars.restore') }}</button>
              </figure>
            </div>
          </section>

          <section ref="lookBox" class="looks" :style="{ order: cur.reference ? 6 : 0 }" :aria-label="$t('imagine.chars.looks')">
            <div class="lh">
              <h3 class="sec">{{ $t('imagine.chars.looks') }}</h3>
              <button type="button" class="btn" :disabled="making || !!looksWhy" @click="doLooks"><Icon name="sparkles" :size="16" /> {{ $t('imagine.chars.makeLooks') }}</button>
            </div>
            <p v-if="looksWhy" class="small muted why">{{ looksWhy }}</p>
            <p v-if="!cur.looks.length" class="small muted">{{ $t('imagine.chars.noLooks') }}</p>
            <div v-else class="strip">
              <button v-for="(l, i) in cur.looks" :key="`${l.job}-${l.n}`" type="button" class="look" :aria-label="l.prompt" @click="emit('view', cur.id, i)">
                <img :src="imagineRaw(l.file)" :alt="l.prompt" loading="lazy" decoding="async">
                <span v-if="cur.reference && cur.reference.job === l.job && cur.reference.n === l.n" class="tag" aria-hidden="true"><Icon name="star" :size="12" /></span>
              </button>
            </div>
          </section>
          </div>
          <p v-else class="small muted why">{{ $t('imagine.chars.saveForLooks') }}</p>
        </Panel>
        <p v-else-if="chars.length" class="empty-state">{{ $t('imagine.chars.pick') }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cgrid { display: grid; grid-template-columns: minmax(0, 1fr); gap: 16px; align-items: start; }
.clist, .ed { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
.new { align-self: flex-start; }
.cards { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.ccard { display: flex; align-items: center; gap: 12px; width: 100%; padding: 8px; text-align: left; font: inherit; color: var(--text); background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); cursor: pointer; transition: border-color var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out); }
.ccard:hover { border-color: var(--line-2); }
.ccard:active { transform: scale(.99); }
.ccard.on { border-color: var(--accent); background: var(--accent-soft); }
.ccard:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.cimg { flex: none; display: flex; align-items: center; justify-content: center; width: 48px; aspect-ratio: 832 / 1216; border-radius: var(--radius-sm); background: var(--panel-2); border: 1px solid var(--line); color: var(--faint); overflow: hidden; }
.cimg img { display: block; width: 100%; height: 100%; object-fit: cover; }
.ctxt { display: flex; flex-direction: column; min-width: 0; }
.cn { font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.form { display: flex; flex-direction: column; gap: 12px; }
.fld { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.fld input, .fld textarea { width: 100%; box-sizing: border-box; }
.fld textarea { resize: vertical; min-height: 64px; }
.fld input[aria-invalid='true'] { border-color: var(--bad); }
.two { display: grid; grid-template-columns: minmax(0, 1fr); gap: 12px; }
.lab { font-size: 12.5px; color: var(--muted); }
.bad { color: var(--bad); }
.seg { align-self: flex-start; max-width: 100%; overflow-x: auto; }
.adult { display: flex; flex-direction: column; gap: 4px; }
.at { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.ah { margin: 0; }
.sw { flex: none; position: relative; width: 44px; height: 26px; padding: 0; border-radius: 13px; border: 1px solid var(--line-2); background: var(--track); cursor: pointer; }
.sw i { position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%; background: var(--muted); transition: transform var(--dur) var(--ease-out); }
.sw.on { background: var(--accent-soft); border-color: var(--accent); }
.sw.on i { transform: translateX(18px); background: var(--accent); }
.sw:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.acts { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.stage { display: flex; flex-direction: column; }
.blk { display: flex; flex-direction: column; gap: 10px; margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--line); }
.ref { display: block; padding: 0; width: 160px; max-width: 60%; aspect-ratio: 832 / 1216; border: 1px solid var(--line); border-radius: var(--radius); background: var(--panel-2); overflow: hidden; cursor: pointer; }
.ref img, .rimg img { display: block; width: 100%; height: 100%; object-fit: cover; }
.ref:focus-visible, .rimg:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.rgrid { display: grid; grid-template-columns: minmax(0, 1fr); gap: 16px; }
.rcard { margin: 0; display: flex; flex-direction: column; gap: 8px; }
.rimg { display: block; padding: 0; width: 100%; aspect-ratio: 832 / 1216; border: 1px solid var(--line); border-radius: var(--radius); background: var(--panel-2); overflow: hidden; cursor: pointer; }
.rbtns { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.rate { justify-content: center; min-height: 44px; font-size: 15px; }
.bar { height: 4px; border-radius: 2px; background: var(--track); overflow: hidden; }
.bar i { display: block; height: 100%; background: var(--accent); transition: width var(--dur) var(--ease-out); }
.sgrid { display: grid; grid-template-columns: repeat(auto-fill, minmax(96px, 1fr)); gap: 8px; }
.scard { position: relative; margin: 0; }
.rm { position: absolute; top: 4px; right: 4px; background: color-mix(in srgb, var(--panel) 82%, transparent); }
.rm2 { position: absolute; left: 4px; right: 4px; bottom: 4px; justify-content: center; background: color-mix(in srgb, var(--panel) 82%, transparent); }
.own { display: flex; align-items: center; gap: 8px; min-height: 24px; cursor: pointer; }
.own input { flex: none; width: 16px; height: 16px; margin: 0; }
.hid { position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none; }
.upq { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 4px; }
.upq li { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.un { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.eline { margin: 0; overflow-wrap: anywhere; }
.up { position: absolute; left: 4px; bottom: 4px; }
.dim img { opacity: .55; }
.head { display: inline-flex; align-items: center; gap: 6px; }
.looks { display: flex; flex-direction: column; gap: 10px; margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--line); }
.lh { display: flex; align-items: center; justify-content: space-between; gap: 8px 12px; flex-wrap: wrap; }
.lh .sec { margin: 0; }
.why { margin: 0; }
.strip { display: grid; grid-template-columns: repeat(auto-fill, minmax(96px, 1fr)); gap: 8px; }
.look { position: relative; display: block; padding: 0; width: 100%; aspect-ratio: 832 / 1216; border: 1px solid var(--line); border-radius: var(--radius-sm); background: var(--panel-2); overflow: hidden; cursor: pointer; transition: transform var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out); }
.look:hover { border-color: var(--line-2); }
.look:active { transform: scale(.98); }
.look:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.look img { display: block; width: 100%; height: 100%; object-fit: cover; }
.tag { position: absolute; left: 6px; bottom: 6px; display: inline-flex; padding: 3px; border-radius: var(--radius-sm); background: color-mix(in srgb, var(--panel) 82%, transparent); color: var(--accent); }
@media (min-width: 700px) {
  .cgrid { grid-template-columns: 280px minmax(0, 1fr); }
  .clist { position: sticky; top: 64px; }
  .two { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (min-width: 560px) { .rgrid { grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); } }
@media (pointer: coarse) {
  .rm { min-width: 36px; min-height: 36px; } .rm2, .head { min-height: 36px; }
  .sw { width: 48px; height: 32px; border-radius: 16px; } .sw i { width: 24px; height: 24px; } .sw.on i { transform: translateX(16px); }
  .own { min-height: 36px; } .own input { width: 20px; height: 20px; }
  .btn, .ccard { min-height: 36px; } .btn.icon { min-width: 36px; }
}
@media (prefers-reduced-motion: reduce) { .sw i, .ccard, .look, .bar i { transition: none; } }
</style>
