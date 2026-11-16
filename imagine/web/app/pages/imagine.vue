<script setup lang="ts">
import type { ImagineEdit, ImagineImage, ImagineJob } from '../composables/useImagine'

const { t } = useI18n()
useHead({ title: `${t('imagine.title')} · Bastion` })
const { toast } = useToast()
const { data, failed, refresh, chars, charsFailed, refreshChars, live, active, submit, cancel, dismiss, remove, editJson, regenerate, saveChar, deleteChar, makeLooks, setReference, makeBatch, rate, uploadPic, removePic, cleanup } = useImagine()
const { armed, arm } = useArm()
const tab = usePageTab('create')
const TABS = computed(() => [{ key: 'create', label: t('imagine.tabs.create'), icon: 'sparkles' }, { key: 'characters', label: t('imagine.tabs.characters'), icon: 'users' }])

const prompt = ref('')
const style = ref('anime') // first-visit defaults: anime, one image (nothing is remembered between visits)
const size = ref('square')
const draft = ref(false)
const count = ref(1)
const adult = ref(false) // Anime only; Draft always uses the safe-tuned small model
const sending = ref(false)
// a character (Anime only): the agent puts its tags before the scene text typed above, adult follows it unless flipped here
const charId = ref('')
const sameLook = ref(true)
const curChar = computed(() => chars.value?.find(c => c.id === charId.value) ?? null)
const canSame = computed(() => !!curChar.value?.reference) // "Match reference" needs the reference picture
watch(charId, () => { if (curChar.value) { adult.value = curChar.value.adult; sameLook.value = true } })
watch(chars, (l) => { if (charId.value && l && !l.some(c => c.id === charId.value)) charId.value = '' })
const STYLES = ['photo', 'anime', 'pixel', 'logo']
const SIZES = ['square', 'portrait', 'landscape', 'phone']

const games = computed(() => !!data.value?.games)
const aiDown = computed(() => !!data.value && data.value.ai_up === false)
const notReady = computed(() => !!data.value && !data.value.ready)
const can = computed(() => !!prompt.value.trim() && !sending.value && !games.value && !notReady.value)
const recent = computed<ImagineJob[]>(() => (data.value?.queue ?? []).filter(j => j.status === 'failed').slice(0, 5))

async function go() {
  if (!can.value) return
  sending.value = true
  const withChar = style.value === 'anime' && !!curChar.value
  const ok = await submit({ prompt: prompt.value.trim(), style: style.value, size: size.value, draft: draft.value, count: count.value, adult: style.value === 'anime' && adult.value, ...(withChar ? { character: charId.value, same_look: sameLook.value && canSame.value } : {}) })
  sending.value = false
  if (ok) toast(t('imagine.submitted'), { tone: 'ok' })
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); go() }
}

const statusWord = (j: ImagineJob) => j.phase === 'freeing' ? t('imagine.freeing') : j.status === 'running' ? t('imagine.running', { n: Math.min(j.done_n + 1, j.count), count: j.count })
  : j.status === 'paused' ? t('imagine.gamesStreaming') : t('imagine.queued')

// gallery grouped by day, newest first
const flat = computed<ImagineImage[]>(() => data.value?.gallery ?? [])
const groups = computed(() => {
  const out: { date: string, items: ImagineImage[] }[] = []
  for (const i of flat.value) {
    const g = out[out.length - 1]
    if (g && g.date === i.date) g.items.push(i)
    else out.push({ date: i.date, items: [i] })
  }
  return out
})
function dayLabel(d: string) {
  const day = new Date(`${d}T12:00:00`)
  const start = (x: Date) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime()
  const diff = Math.round((start(new Date()) - start(day)) / 86_400_000)
  return diff === 0 ? t('imagine.today') : diff === 1 ? t('imagine.yesterday') : fmtDate(day)
}

// viewer
const open = ref(-1)
const lookChar = ref('') // set while the viewer walks one character's looks (from the Characters tab) instead of the whole gallery
const list = computed<ImagineImage[]>(() => lookChar.value ? (chars.value?.find(c => c.id === lookChar.value)?.looks ?? []) : flat.value)
const cur = computed(() => (open.value >= 0 ? list.value[open.value] : null))
const step = (d: number) => { const n = open.value + d; if (n >= 0 && n < list.value.length) open.value = n }
const openGallery = (i: ImagineImage) => { lookChar.value = ''; open.value = flat.value.indexOf(i) }
const openLook = (id: string, i: number) => { lookChar.value = id; open.value = i }
watch(open, (v) => { if (v < 0) lookChar.value = '' })
const isRef = computed(() => { const r = chars.value?.find(c => c.id === lookChar.value)?.reference; return !!r && !!cur.value && r.job === cur.value.job && r.n === cur.value.n })
const settingRef = ref(false)
async function useAsRef() {
  const img = cur.value
  if (!img || !lookChar.value || settingRef.value) return
  settingRef.value = true
  try { await setReference(lookChar.value, img); toast(t('imagine.chars.referenceSet'), { tone: 'ok' }) } catch (e: any) { toast(apiErr(e), { tone: 'bad' }) }
  settingRef.value = false
}
function reuse(i: ImagineImage) {
  const c = i.character ? chars.value?.find(x => x.id === i.character) : null
  charId.value = ''
  prompt.value = c ? i.scene : i.prompt
  if (STYLES.includes(i.style)) style.value = i.style
  if (SIZES.includes(i.size)) size.value = i.size
  draft.value = i.draft
  adult.value = !!i.adult
  open.value = -1
  tab.value = 'create'
  if (c && i.style === 'anime') nextTick(() => { charId.value = c.id; adult.value = !!i.adult })
  nextTick(() => window.scrollTo({ top: 0, behavior: 'smooth' }))
}
async function del(i: ImagineImage) {
  if (!arm(`${i.job}-${i.n}`)) return
  const at = open.value
  if (await remove(i)) {
    toast(t('imagine.deleted'), { tone: 'ok' })
    await refreshChars()
    open.value = list.value.length ? Math.min(at, list.value.length - 1) : -1
  }
}

// edit panel: the image's prompt as five groups of fields, edited by hand (no AI), regenerated with a new seed
const FIELDS = ['subject', 'setting', 'composition', 'lighting', 'colors', 'mood'] as const
type Field = typeof FIELDS[number]
// Scene keeps the time of day inside setting; Look has three fields, the others one
const GROUPS: { id: string, fields: Field[], rows: number }[] = [
  { id: 'subject', fields: ['subject'], rows: 2 },
  { id: 'scene', fields: ['setting'], rows: 2 },
  { id: 'look', fields: ['lighting', 'colors', 'mood'], rows: 2 },
  { id: 'shot', fields: ['composition'], rows: 2 },
]
const edit = reactive<Record<Field, string>>({ subject: '', setting: '', composition: '', lighting: '', colors: '', mood: '' })
const detailsText = ref('')
const editState = ref<'loading' | 'ready' | 'error'>('loading')
const editErr = ref('')
const keep = ref(false)
const editAdult = ref(false)
const regenerating = ref(false)
let editTimer: any
let editSeq = 0
const apiErr = (e: any) => e?.data?.statusMessage || e?.message || t('imagine.failed')
function fill(j: ImagineEdit) {
  for (const k of FIELDS) edit[k] = j[k] || ''
  detailsText.value = (j.details || []).join('\n')
}
const gather = (): ImagineEdit => ({ ...edit, details: detailsText.value.split('\n').map(x => x.trim()).filter(Boolean) })
function loadEdit(img: ImagineImage | null) {
  clearTimeout(editTimer)
  const seq = ++editSeq
  keep.value = false
  editAdult.value = !!img?.adult
  editState.value = 'loading'
  if (!img) return
  editTimer = setTimeout(async () => { // a short pause so stepping through images does not call the local AI for each one
    try {
      const r = await editJson(img)
      if (seq !== editSeq) return
      fill(r.json)
      editState.value = 'ready'
    } catch (e: any) {
      if (seq !== editSeq) return
      editErr.value = apiErr(e)
      editState.value = 'error'
    }
  }, 250)
}
watch(() => (cur.value ? `${cur.value.job}-${cur.value.n}` : ''), () => loadEdit(cur.value))
onBeforeUnmount(() => clearTimeout(editTimer))
const blocked = computed(() => active.value ? t('imagine.editBusy') : '')
const regenBlocked = computed(() => blocked.value || (games.value ? t('imagine.gamesStreaming') : ''))
async function regen() {
  const img = cur.value
  if (!img || regenerating.value || regenBlocked.value) return
  regenerating.value = true
  const ok = await regenerate(img, gather(), keep.value, editAdult.value)
  regenerating.value = false
  if (ok) { toast(t('imagine.submitted'), { tone: 'ok' }); open.value = -1 }
}
const parent = computed(() => {
  const p = cur.value?.parent
  return p ? list.value.findIndex(i => i.job === p.job && i.n === p.n) : -1
})
function viewerKey(e: KeyboardEvent) {
  if (open.value < 0) return
  if ((e.target as HTMLElement)?.closest?.('textarea, input')) { if (e.key === 'Escape') open.value = -1; return }
  if (e.key === 'Escape') open.value = -1
  else if (e.key === 'ArrowLeft') step(-1)
  else if (e.key === 'ArrowRight') step(1)
}
onMounted(() => window.addEventListener('keydown', viewerKey))
onBeforeUnmount(() => window.removeEventListener('keydown', viewerKey))
const looksBlocked = computed(() => active.value ? t('imagine.editBusy') : games.value ? t('imagine.gamesStreaming') : notReady.value ? t('imagine.notReady') : '')
const dlName = (i: ImagineImage) => `imagine-${i.date}-${i.job}-${i.n}.png`
</script>

<template>
  <div>
    <PageTabs v-model="tab" :tabs="TABS" />
    <div v-if="aiDown" class="row notice">
      <span class="small muted">{{ $t('imagine.aiDown') }}</span>
      <button class="btn sm" @click="refresh()">{{ $t('imagine.retry') }}</button>
    </div>
    <ImagineCharacters v-if="tab === 'characters'" :chars="chars" :failed="charsFailed" :blocked="looksBlocked" :save="saveChar" :remove="deleteChar" :looks="makeLooks" :batch="makeBatch" :rate="rate" :upload="uploadPic" :remove-pic="removePic" :cleanup="cleanup" @view="openLook" />
    <div v-show="tab !== 'characters'" class="im">
    <div class="side">
      <h2 class="sec"><Icon name="image" :size="18" /> {{ $t('imagine.title') }}</h2>
      <Panel :title="$t('imagine.prompt')" id="imagine-form">
        <form class="form" @submit.prevent="go">
          <textarea v-model="prompt" rows="4" maxlength="1000" :placeholder="$t('imagine.promptHint')" :aria-label="$t('imagine.prompt')" @keydown="onKey" />
          <div class="row">
            <span class="lab">{{ $t('imagine.style') }}</span>
            <div class="seg"><button v-for="s in STYLES" :key="s" type="button" :class="{ on: style === s }" @click="style = s">{{ $t(`imagine.styles.${s}`) }}</button></div>
          </div>
          <div v-if="style === 'anime' && chars?.length" class="charsel">
            <label class="row"><span class="lab">{{ $t('imagine.chars.character') }}</span>
              <select v-model="charId" :aria-label="$t('imagine.chars.character')"><option value="">{{ $t('imagine.chars.none') }}</option><option v-for="c in chars" :key="c.id" :value="c.id">{{ c.name }}</option></select>
            </label>
            <template v-if="curChar">
              <label class="chk small"><input v-model="sameLook" type="checkbox" :disabled="!canSame"> {{ $t('imagine.chars.sameLook') }}</label>
              <p v-if="!canSame" class="small muted ah">{{ $t('imagine.chars.sameLookNeeds') }}</p>
            </template>
          </div>
          <div v-if="style === 'anime'" class="adult">
            <div class="at"><span class="lab">{{ $t('imagine.adult') }}</span><button type="button" class="sw" :class="{ on: adult }" role="switch" :aria-checked="adult" :aria-label="$t('imagine.adult')" @click="adult = !adult"><i /></button></div>
            <p class="small muted ah">{{ $t('imagine.adultHint') }}</p>
          </div>
          <div class="row">
            <span class="lab">{{ $t('imagine.size') }}</span>
            <div class="seg"><button v-for="s in SIZES" :key="s" type="button" :class="{ on: size === s }" @click="size = s">{{ $t(`imagine.sizes.${s}`) }}</button></div>
          </div>
          <div class="row">
            <button type="button" class="chip" :class="{ on: draft }" :aria-pressed="draft" @click="draft = !draft">{{ $t('imagine.draft') }}</button>
            <div class="seg"><button type="button" :class="{ on: count === 4 }" @click="count = 4">{{ $t('imagine.make4') }}</button><button type="button" :class="{ on: count === 1 }" @click="count = 1">{{ $t('imagine.make1') }}</button></div>
          </div>
          <button type="submit" class="btn primary go" :disabled="!can"><Icon name="sparkles" :size="16" /> {{ $t('imagine.generate') }}</button>
          <p v-if="games" class="pill warn note"><Icon name="pause" :size="14" /> {{ $t('imagine.gamesStreaming') }}</p>
          <p v-else-if="notReady" class="small muted">{{ $t('imagine.notReady') }}</p>
        </form>
      </Panel>

      <Panel v-if="live.length || recent.length" :title="$t('imagine.queue')" id="imagine-queue">
        <ul class="jobs">
          <li v-for="j in live" :key="j.id" class="job">
            <div class="jt">
              <span class="dot" :class="j.status === 'running' ? 'ok' : j.status === 'paused' ? 'warn' : ''" />
              <span class="jp">{{ j.prompt }}</span>
              <button type="button" class="btn ghost sm icon" :aria-label="$t('imagine.cancel')" @click="cancel(j.id)"><Icon name="x" :size="16" /></button>
            </div>
            <div class="js small muted">{{ statusWord(j) }}</div>
            <div v-if="data?.voice_paused" class="js small muted">{{ $t('imagine.voicePaused') }}</div>
            <div class="bar" aria-hidden="true"><i :style="{ width: `${(j.done_n / j.count) * 100}%` }" /></div>
          </li>
          <li v-for="j in recent" :key="j.id" class="job">
            <div class="errbox small errrow">
              <span>{{ j.error || $t('imagine.failed') }}</span>
              <button type="button" class="btn ghost sm icon" :aria-label="$t('imagine.dismiss')" @click="dismiss(j.id)"><Icon name="x" :size="16" /></button>
            </div>
          </li>
        </ul>
      </Panel>
    </div>

    <div class="main">
      <div v-if="failed && !data" class="errbox">{{ failed }}</div>
      <Skeleton v-else-if="!data" kind="tiles" :n="6" />
      <p v-else-if="!flat.length" class="empty-state">{{ $t('imagine.empty') }}</p>
      <template v-else>
        <section v-for="g in groups" :key="g.date" class="day">
          <h3 class="sec">{{ dayLabel(g.date) }}</h3>
          <div class="tiles">
            <button v-for="i in g.items" :key="`${i.job}-${i.n}`" type="button" class="tile" :style="{ aspectRatio: imagineRatio(i.size) }" :aria-label="i.prompt" @click="openGallery(i)">
              <img :src="imagineRaw(i.file)" :alt="i.prompt" loading="lazy" decoding="async">
              <span v-if="i.parent" class="tag" aria-hidden="true"><Icon name="rotate-ccw" :size="12" /></span>
            </button>
          </div>
        </section>
      </template>
    </div>
    </div>

    <Teleport to="body">
      <div v-if="cur" class="viewer" role="dialog" aria-modal="true" @click.self="open = -1">
        <div class="vbox">
          <div class="vimg" @click.self="open = -1"><img :key="cur.file" :src="imagineRaw(cur.file)" :alt="cur.prompt"></div>
          <p class="vp">{{ cur.prompt }}</p>
          <p v-if="parent >= 0" class="vfrom small"><button type="button" class="lnk" @click="open = parent">{{ $t('imagine.from') }}</button></p>
          <div class="vact">
            <button type="button" class="btn ghost icon" :aria-label="$t('imagine.prev')" :disabled="open <= 0" @click="step(-1)"><Icon name="chevron-left" :size="18" /></button>
            <a class="btn" :href="imagineRaw(cur.file)" :download="dlName(cur)"><Icon name="download" :size="16" /> {{ $t('imagine.download') }}</a>
            <button v-if="lookChar" type="button" class="btn" :disabled="isRef || settingRef" @click="useAsRef"><Icon name="star" :size="16" /> {{ isRef ? $t('imagine.chars.isReference') : $t('imagine.chars.useAsReference') }}</button>
            <button type="button" class="btn" @click="reuse(cur)"><Icon name="rotate-ccw" :size="16" /> {{ $t('imagine.reuse') }}</button>
            <button type="button" class="btn danger" :class="{ sure: armed === `${cur.job}-${cur.n}` }" @click="del(cur)"><Icon name="trash-2" :size="16" /> {{ armed === `${cur.job}-${cur.n}` ? $t('imagine.sure') : $t('imagine.delete') }}</button>
            <button type="button" class="btn ghost icon" :aria-label="$t('imagine.next')" :disabled="open >= list.length - 1" @click="step(1)"><Icon name="chevron-right" :size="18" /></button>
          </div>
          <section class="edit" :aria-label="$t('imagine.edit.title')">
            <h3 class="sec"><Icon name="pencil" :size="16" /> {{ $t('imagine.edit.title') }}</h3>
            <Skeleton v-if="editState === 'loading'" kind="lines" :n="4" />
            <div v-else-if="editState === 'error'" class="errbox small">{{ editErr }}</div>
            <template v-else>
              <div class="groups">
                <section v-for="g in GROUPS" :key="g.id" class="grp" :aria-labelledby="`imedit-${g.id}`">
                  <h4 :id="`imedit-${g.id}`" class="gh">{{ $t(`imagine.edit.groups.${g.id}.label`) }}</h4>
                  <p class="small muted gp">{{ $t(`imagine.edit.groups.${g.id}.hint`) }}</p>
                  <label v-for="f in g.fields" :key="f" class="fld"><span v-if="g.fields.length > 1" class="lab">{{ $t(`imagine.edit.fields.${f}`) }}</span><textarea v-model="edit[f]" :rows="g.rows" maxlength="200" :aria-label="g.fields.length > 1 ? $t(`imagine.edit.fields.${f}`) : $t(`imagine.edit.groups.${g.id}.label`)" /></label>
                </section>
                <section class="grp" aria-labelledby="imedit-extras">
                  <h4 id="imedit-extras" class="gh">{{ $t('imagine.edit.groups.extras.label') }}</h4>
                  <p class="small muted gp">{{ $t('imagine.edit.groups.extras.hint') }}</p>
                  <textarea v-model="detailsText" rows="4" :aria-label="$t('imagine.edit.groups.extras.label')" />
                </section>
              </div>
              <div v-if="cur.style === 'anime'" class="adult">
                <div class="at"><span class="lab">{{ $t('imagine.adult') }}</span><button type="button" class="sw" :class="{ on: editAdult }" role="switch" :aria-checked="editAdult" :aria-label="$t('imagine.adult')" @click="editAdult = !editAdult"><i /></button></div>
                <p class="small muted ah">{{ $t('imagine.adultHint') }}</p>
              </div>
              <div class="regen">
                <label class="chk small"><input v-model="keep" type="checkbox"> {{ $t('imagine.edit.keepSeed') }}</label>
                <button type="button" class="btn primary" :disabled="regenerating || !!regenBlocked" @click="regen"><Icon name="refresh-cw" :size="16" /> {{ $t('imagine.edit.regenerate') }}</button>
              </div>
              <p v-if="regenBlocked" class="small muted why">{{ regenBlocked }}</p>
            </template>
          </section>
          <button type="button" class="btn ghost icon vclose" :aria-label="$t('imagine.close')" @click="open = -1"><Icon name="x" :size="18" /></button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.notice { padding: 8px 12px; margin-bottom: 12px; border: 1px solid var(--line); border-left: 3px solid var(--warn); border-radius: var(--radius-sm); background: var(--panel); }
.im { display: grid; grid-template-columns: minmax(0, 1fr); gap: 16px; align-items: start; }
.side, .main { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
.side .sec { margin: 0; display: flex; align-items: center; gap: 8px; }
.form { display: flex; flex-direction: column; gap: 12px; }
.form textarea { width: 100%; resize: vertical; min-height: 92px; box-sizing: border-box; }
.row { display: flex; align-items: center; justify-content: space-between; gap: 8px 12px; flex-wrap: wrap; }
.lab { font-size: 12.5px; color: var(--muted); }
.row .seg { max-width: 100%; overflow-x: auto; }
.adult { display: flex; flex-direction: column; gap: 4px; }
.at { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.ah { margin: 0; }
.charsel { display: flex; flex-direction: column; gap: 6px; }
.charsel select { max-width: 60%; min-width: 0; }
.sw { flex: none; position: relative; width: 44px; height: 26px; padding: 0; border-radius: 13px; border: 1px solid var(--line-2); background: var(--track); cursor: pointer; }
.sw i { position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%; background: var(--muted); transition: transform var(--dur) var(--ease-out); }
.sw.on { background: var(--accent-soft); border-color: var(--accent); }
.sw.on i { transform: translateX(18px); background: var(--accent); }
.sw:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.go { width: 100%; justify-content: center; }
.note { align-self: flex-start; margin: 0; white-space: normal; }
.jobs { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 12px; }
.job { display: flex; flex-direction: column; gap: 4px; }
.jt { display: flex; align-items: center; gap: 8px; min-width: 0; }
.errrow { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.jp { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13.5px; }
.bar { height: 4px; border-radius: 2px; background: var(--track); overflow: hidden; }
.bar i { display: block; height: 100%; background: var(--accent); transition: width .4s var(--ease-out); }
.day { display: flex; flex-direction: column; gap: 8px; }
.day .sec { margin: 0; }
.tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; align-items: start; }
.tile { padding: 0; border: 1px solid var(--line); border-radius: var(--radius-sm); background: var(--panel-2); overflow: hidden; cursor: pointer; display: block; width: 100%; transition: transform var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out); }
.tile:hover { border-color: var(--line-2); }
.tile:active { transform: scale(.98); }
.tile:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.tile img { display: block; width: 100%; height: 100%; object-fit: cover; }
.tile { position: relative; }
.tag { position: absolute; left: 6px; bottom: 6px; display: inline-flex; padding: 3px; border-radius: var(--radius-sm); background: color-mix(in srgb, var(--panel) 82%, transparent); color: var(--muted); }
.viewer { position: fixed; inset: 0; z-index: 60; background: color-mix(in srgb, var(--bg) 88%, transparent); display: flex; padding: 12px; overflow-y: auto; overscroll-behavior: contain; animation: imfade var(--dur) var(--ease-out); }
.vbox { position: relative; display: flex; flex-direction: column; gap: 10px; width: min(100%, 960px); margin: auto; }
.vfrom { margin: 0; text-align: center; }
.edit { display: flex; flex-direction: column; gap: 10px; padding: 12px; border: 1px solid var(--line); border-radius: var(--radius); background: var(--panel); }
.edit .sec { margin: 0; display: flex; align-items: center; gap: 8px; }
.groups { display: grid; grid-template-columns: minmax(0, 1fr); gap: 0 16px; }
.grp { display: flex; flex-direction: column; gap: 6px; min-width: 0; padding: 12px 0; border-top: 1px solid var(--line); }
.grp:first-child { border-top: 0; padding-top: 0; }
.gh { margin: 0; font-size: 13.5px; font-weight: 600; }
.gp { margin: 0; }
.fld { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.grp textarea { width: 100%; box-sizing: border-box; resize: vertical; min-height: 40px; }
.regen { display: flex; align-items: center; justify-content: space-between; gap: 8px 12px; flex-wrap: wrap; }
.chk { display: inline-flex; align-items: center; gap: 8px; color: var(--muted); cursor: pointer; }
.why { margin: 0; }
.vimg { display: flex; justify-content: center; min-height: 0; }
.vimg img { max-width: 100%; max-height: calc(100dvh - 190px); object-fit: contain; border-radius: var(--radius-sm); border: 1px solid var(--line); background: var(--panel); }
.vp { margin: 0; font-size: 13.5px; color: var(--muted); text-align: center; overflow-wrap: anywhere; max-height: 4.5em; overflow-y: auto; }
.vact { display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap; }
.vclose { position: absolute; top: 0; right: 0; background: var(--panel); }
@keyframes imfade { from { opacity: 0; } }
@media (min-width: 700px) { .groups { grid-template-columns: repeat(2, minmax(0, 1fr)); } .grp:nth-child(2) { border-top: 0; padding-top: 0; } }
@media (min-width: 960px) {
  .im { grid-template-columns: 360px minmax(0, 1fr); }
  .side { position: sticky; top: 12px; }
}
@media (max-width: 640px) { .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (pointer: coarse) { .sw { width: 48px; height: 32px; border-radius: 16px; } .sw i { width: 24px; height: 24px; } .sw.on i { transform: translateX(16px); } .vact .btn, .row .btn, .edit .btn { min-height: 36px; } .chk { min-height: 36px; } .chk input { width: 20px; height: 20px; } .vfrom .lnk { min-height: 32px; } .btn.icon { min-width: 36px; min-height: 36px; } }
@media (prefers-reduced-motion: reduce) { .viewer { animation: none; } .sw i { transition: none; } .bar i { transition: none; } }
</style>
