<script setup lang="ts">
const { t } = useI18n()
useHead({ title: () => `${t('designs.title')} · pve` })
const { toast } = useToast()
const { armed, arm } = useArm()

type Design = { id: number, uid: number, author: string, name: string, tokens: DesignTokens, css: string, skin: string, shared: boolean, users: number }
type Preset = { key: string, name: string, tokens: DesignTokens, css?: string, skin?: string }
type Data = { mine: Design[], gallery: Design[], presets: Preset[], pick: string, own: boolean }
type Cat = { slug: string, name: string, author: string, tokens: DesignTokens, css: string, skin: string }
const data = ref<Data | null>(null)
const err = ref('')
const why = (e: any) => e?.data?.statusMessage || e?.statusMessage || e?.message || 'failed'

// phone / tablet / desktop: with a design of its own, picks here only change this kind of device
const device = deviceKind()
async function load() {
  try { data.value = await $fetch<Data>('/api/designs', { query: { device } }); err.value = '' } catch (e) { err.value = why(e) }
}
onMounted(load)

const lookOf = (x?: { tokens: DesignTokens, css?: string, skin?: string } | null): Look | null =>
  x ? { tokens: x.tokens, css: x.css ?? '', skin: x.skin ?? '' } : null
const lookOfPick = (pick: string) => {
  const d = data.value
  if (!d || pick === 'p:default') return null
  if (pick.startsWith('p:')) return lookOf(d.presets.find(p => `p:${p.key}` === pick))
  return lookOf([...d.mine, ...d.gallery].find(x => `d:${x.id}` === pick))
}
// skins installed here (skin add-ons register a built-in look that names them)
const skins = computed(() => (data.value?.presets ?? []).filter(p => p.skin).map(p => ({ id: p.skin!, name: p.name })))
const skinMissing = (s?: string) => !!s && !skins.value.some(k => k.id === s)
const skinLine = (s?: string) => (!s ? '' : skinMissing(s) ? t('designs.skinMissing', { skin: s }) : t('designs.skinOn', { skin: skins.value.find(k => k.id === s)!.name }))
const sub = (...parts: string[]) => parts.filter(Boolean).join(' · ')

async function use(pick: string) {
  if (!data.value || draft.value) return
  const before = data.value.pick
  data.value.pick = pick
  applyLook(lookOfPick(pick))
  try { applyLook((await $fetch<any>('/api/designs/pick', { method: 'POST', body: { pick, device: data.value.own ? device : undefined } })).look); load() } catch (e) {
    data.value.pick = before
    applyLook(lookOfPick(before))
    toast(why(e), { tone: 'bad' })
  }
}

// "Only on this phone": keeps the design in use now as this device's own; "Every device" goes back to the account's
async function setOwn(on: boolean) {
  if (!data.value || draft.value || on === data.value.own) return
  try {
    applyLook((await $fetch<any>('/api/designs/pick', { method: 'POST', body: { pick: on ? data.value.pick : 'follow', device } })).look)
    await load()
  } catch (e) { toast(why(e), { tone: 'bad' }) }
}

// the editor: changes paint the whole app live, Cancel puts the design in use back
type Draft = { id?: number, name: string, tokens: DesignTokens, css: string, skin: string, shared: boolean }
const draft = ref<Draft | null>(null)
const saving = ref(false)
function startEdit(d?: Design, from?: Look | null, name?: string) {
  const base = lookOf(d) ?? from ?? lookOfPick(data.value?.pick ?? 'p:default') ?? lookOf(data.value!.presets[0])!
  draft.value = { id: d?.id, name: d?.name ?? name ?? t('designs.new'), tokens: { ...base.tokens }, css: base.css ?? '', skin: base.skin ?? '', shared: d?.shared ?? false }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
watch(draft, (d) => { if (d) applyLook(lookOf(d), false) }, { deep: true })
function cancel() {
  draft.value = null
  aiJob.value = ''
  applyLook(lookOfPick(data.value?.pick ?? 'p:default'))
}
async function save() {
  if (!draft.value) return
  saving.value = true
  try {
    const d = await $fetch<Design>('/api/designs', { method: 'POST', body: draft.value })
    draft.value = null
    await load()
    await use(`d:${d.id}`) // what you were looking at becomes the one in use
    toast(t('designs.saved'), { tone: 'ok' })
  } catch (e) { toast(why(e), { tone: 'bad' }) } finally { saving.value = false }
}

// images for the design (uploaded to this dashboard; the stylesheet refers to them with url(/api/designs/img/…))
const images = computed(() => [...new Set([...(draft.value?.css ?? '').matchAll(/\/api\/designs\/img\/[a-f0-9]{24}\.[a-z]+/g)].map(m => m[0]))])
const uploading = ref(false)
async function addImage(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  ;(e.target as HTMLInputElement).value = ''
  if (!f || !draft.value) return
  uploading.value = true
  try {
    const data = await new Promise<string>((ok, no) => { const r = new FileReader(); r.onload = () => ok(String(r.result)); r.onerror = no; r.readAsDataURL(f) })
    const { url } = await $fetch<{ url: string }>('/api/designs/img', { method: 'POST', body: { data } })
    // the first image becomes the page background; later ones are listed for the stylesheet (and for Claude)
    const bg = images.value.length ? '' : `\n:root:root:root body { background: url(${url}) center / cover fixed; }\n`
    draft.value.css = `${draft.value.css}${bg || `\n/* image: url(${url}) */\n`}`
    toast(t('designs.imageAdded'), { tone: 'ok' })
  } catch (err) { toast(why(err), { tone: 'bad' }) } finally { uploading.value = false }
}

// "Describe a look": Claude writes colours + stylesheet (+ a skin) into the editor; owner only (it uses the Claude plan)
const ask = ref('')
const aiJob = ref('')
const aiSecs = ref(0)
let aiTimer: any
async function describe() {
  if (!ask.value.trim()) return
  if (!draft.value) startEdit()
  try {
    aiJob.value = (await $fetch<any>('/api/designs/ai', { method: 'POST', body: { ask: ask.value, base: draft.value, images: images.value } })).job
    aiSecs.value = 0
    poll()
  } catch (e) { toast(why(e), { tone: 'bad' }) }
}
async function poll() {
  clearTimeout(aiTimer)
  if (!aiJob.value) return
  let r: any
  try { r = await $fetch<any>(`/api/designs/ai?job=${aiJob.value}`) } catch { r = { state: 'running' } }
  if (r.state === 'running') { aiSecs.value = r.secs ?? aiSecs.value; aiTimer = setTimeout(poll, 3000); return }
  aiJob.value = ''
  if (r.state !== 'done') return toast(r.error || t('designs.aiFailed'), { tone: 'bad' })
  if (!draft.value) startEdit()
  Object.assign(draft.value!, { name: r.design.name, tokens: r.design.tokens, css: r.design.css, skin: r.design.skin })
  toast(r.warning || t('designs.aiDone'), { tone: r.warning ? 'warn' : 'ok' })
}
onUnmounted(() => clearTimeout(aiTimer))

async function share(d: Design) {
  const was = d.shared
  d.shared = !was
  try { await $fetch('/api/designs', { method: 'POST', body: { ...d, shared: !was } }) } catch (e) { d.shared = was; toast(why(e), { tone: 'bad' }) }
}

async function remove(d: Design) {
  if (!arm(`del${d.id}`)) return
  try {
    await $fetch(`/api/designs/${d.id}`, { method: 'DELETE' })
    await load()
    applyLook(lookOfPick(data.value?.pick ?? 'p:default'))
  } catch (e) { toast(why(e), { tone: 'bad' }) }
}

async function copyCode(d: Design) {
  try { await navigator.clipboard.writeText(designCode(d.name, lookOf(d)!)); toast(t('designs.codeCopied'), { tone: 'ok' }) } catch (e) { toast(why(e), { tone: 'bad' }) }
}

const importing = ref(false)
const code = ref('')
function doImport() {
  const d = readDesignCode(code.value)
  if (!d) return toast(t('designs.badCode'), { tone: 'bad' })
  importing.value = false
  code.value = ''
  startEdit(undefined, d, d.name)
}

const usersLine = (d: Design) => t('designs.users', d.users)
const isOwner = computed(() => useAddons().role.value === 'owner')

// the marketplace catalogue (designs published to GitHub from any install); Add = a copy in your designs, in use at once
const cat = ref<Cat[] | null>(null)
const catQ = ref('')
async function loadCat(fresh = false) {
  try { cat.value = (await $fetch<any>(`/api/designs/catalogue${fresh ? '?fresh=1' : ''}`)).designs } catch { cat.value ??= [] }
}
onMounted(() => loadCat())
const catShown = computed(() => {
  const q = catQ.value.trim().toLowerCase()
  return (cat.value ?? []).filter(d => !q || `${d.name} ${d.author}`.toLowerCase().includes(q))
})
async function add(d: Cat) {
  try {
    const n = await $fetch<Design>('/api/designs', { method: 'POST', body: { name: d.name, tokens: d.tokens, css: d.css, skin: d.skin } })
    await load()
    await use(`d:${n.id}`)
    toast(t('designs.added'), { tone: 'ok' })
  } catch (e) { toast(why(e), { tone: 'bad' }) }
}
// Describe + the editor stay above the tabs, so an open draft is visible whichever tab you are on
const tab = usePageTab('yours')
const tabs = computed(() => [
  { key: 'yours', label: t('designs.tabYours') },
  { key: 'builtin', label: t('designs.builtin') },
  { key: 'market', label: t('designs.market') },
  { key: 'shared', label: t('designs.tabShared') },
])
const publish = (d: Design) => useConfirm().ask('design_publish', { id: d.id, name: d.name }, t('designs.publishLabel', { name: d.name }))
</script>

<template>
  <div>
    <div v-if="err" class="errbox">{{ err }}</div>
    <Skeleton v-else-if="!data" kind="cards" :n="4" />
    <div v-else class="stack">
      <Panel v-if="isOwner" :title="$t('designs.describe')" fold="phone">
        <div class="ed">
          <textarea v-model="ask" rows="2" :placeholder="$t('designs.describeHint')" :disabled="!!aiJob" />
          <div class="row">
            <button class="btn primary" :disabled="!ask.trim() || !!aiJob" @click="describe">
              <Icon name="spark" :size="15" />{{ aiJob ? $t('designs.aiWorking', { s: aiSecs }) : $t('designs.generate') }}
            </button>
            <span class="faint small">{{ $t('designs.describeNote') }}</span>
          </div>
        </div>
      </Panel>

      <Panel v-if="draft" :title="draft.id ? $t('designs.edit') : $t('designs.new')" :sub="$t('designs.editing')">
        <div class="ed">
          <label class="fld">
            <span class="faint small">{{ $t('designs.name') }}</span>
            <input v-model="draft.name" maxlength="40">
          </label>
          <div class="row">
            <div class="seg">
              <button :class="{ on: draft.tokens.scheme !== 'light' }" @click="draft.tokens.scheme = 'dark'">{{ $t('designs.dark') }}</button>
              <button :class="{ on: draft.tokens.scheme === 'light' }" @click="draft.tokens.scheme = 'light'">{{ $t('designs.light') }}</button>
            </div>
            <label class="rad">
              <span class="faint small">{{ $t('designs.corners') }}</span>
              <input v-model.number="draft.tokens.radius" type="range" min="0" max="24">
              <span class="mono small">{{ `${draft.tokens.radius}px` }}</span>
            </label>
          </div>
          <div class="faint small">{{ $t('designs.skin') }}</div>
          <div class="row">
            <button class="chip" :class="{ on: !draft.skin }" @click="draft.skin = ''">{{ $t('designs.noSkin') }}</button>
            <button v-for="k in skins" :key="k.id" class="chip" :class="{ on: draft.skin === k.id }" @click="draft.skin = k.id">{{ k.name }}</button>
            <span v-if="skinMissing(draft.skin)" class="pill warn">{{ skinLine(draft.skin) }}</span>
          </div>
          <div class="faint small">{{ $t('designs.colors') }}</div>
          <div class="colors">
            <label v-for="k in DESIGN_COLORS" :key="k" class="col">
              <input v-model="draft.tokens[k]" type="color">
              <span class="small">{{ $t(`designs.c.${k}`) }}</span>
            </label>
          </div>
          <label class="fld">
            <span class="faint small">{{ $t('designs.css') }}</span>
            <textarea v-model.lazy="draft.css" class="mono css" rows="8" spellcheck="false" :placeholder="$t('designs.cssHint')" />
          </label>
          <div class="row">
            <label class="btn sm" :class="{ disabled: uploading }">
              <Icon name="image" :size="15" />{{ uploading ? $t('designs.uploading') : $t('designs.addImage') }}
              <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" hidden :disabled="uploading" @change="addImage">
            </label>
            <img v-for="u in images" :key="u" :src="u" class="thumb" alt="">
          </div>
          <button class="chip" :class="{ on: draft.shared }" @click="draft.shared = !draft.shared">{{ $t('designs.share') }}</button>
          <div class="row">
            <button class="btn primary" :disabled="saving || !draft.name.trim()" @click="save">{{ $t('designs.save') }}</button>
            <button class="btn ghost" @click="cancel">{{ $t('designs.cancel') }}</button>
          </div>
        </div>
      </Panel>

      <div>
      <div class="where">
        <span class="faint small">{{ $t('designs.appliesTo') }}</span>
        <div class="seg">
          <button :class="{ on: !data.own }" :disabled="!!draft" @click="setOwn(false)">{{ $t('designs.everyDevice') }}</button>
          <button :class="{ on: data.own }" :disabled="!!draft" @click="setOwn(true)">{{ $t(`designs.onlyThis.${device}`) }}</button>
        </div>
      </div>
      <PageTabs v-model="tab" :tabs="tabs" />
      <Panel v-if="tab === 'yours'" :title="$t('designs.yours')">
        <template #actions>
          <button class="btn sm" :disabled="!!draft" @click="startEdit()">{{ $t('designs.new') }}</button>
          <button class="btn sm ghost" :disabled="!!draft" @click="importing = !importing">{{ $t('designs.import') }}</button>
        </template>
        <div v-if="importing" class="row imp">
          <input v-model="code" :placeholder="$t('designs.importHint')" class="mono" @keydown.enter="doImport">
          <button class="btn sm" :disabled="!code.trim()" @click="doImport">{{ $t('designs.import') }}</button>
        </div>
        <p v-if="!data.mine.length" class="empty-state">{{ $t('designs.empty') }}</p>
        <div class="cards">
          <DesignCard v-for="d in data.mine" :key="d.id" :name="d.name" :tokens="d.tokens" :active="data.pick === `d:${d.id}`" :sub="sub(skinLine(d.skin), d.shared ? `${$t('designs.sharedPill')} · ${usersLine(d)}` : '')">
            <button v-if="data.pick !== `d:${d.id}`" class="btn sm primary" :disabled="!!draft" @click="use(`d:${d.id}`)">{{ $t('designs.use') }}</button>
            <button class="btn sm" :disabled="!!draft" @click="startEdit(d)">{{ $t('designs.edit') }}</button>
            <button class="chip" :class="{ on: d.shared }" @click="share(d)">{{ $t('designs.sharedPill') }}</button>
            <button class="btn sm ghost" @click="copyCode(d)">{{ $t('designs.code') }}</button>
            <button v-if="isOwner" class="btn sm ghost" @click="publish(d)">{{ $t('designs.publish') }}</button>
            <button class="btn sm ghost sure" :class="{ danger: armed === `del${d.id}` }" @click="remove(d)">{{ armed === `del${d.id}` ? $t('designs.sure') : $t('designs.delete') }}</button>
          </DesignCard>
        </div>
      </Panel>

      <Panel v-else-if="tab === 'builtin'" :title="$t('designs.builtin')">
        <div class="cards">
          <DesignCard v-for="p in data.presets" :key="p.key" :name="p.name" :tokens="p.tokens" :active="data.pick === `p:${p.key}`" :sub="skinLine(p.skin)">
            <button v-if="data.pick !== `p:${p.key}`" class="btn sm primary" :disabled="!!draft" @click="use(`p:${p.key}`)">{{ $t('designs.use') }}</button>
            <button class="btn sm" :disabled="!!draft" @click="startEdit(undefined, lookOf(p), $t('designs.copyName', { name: p.name }))">{{ $t('designs.copy') }}</button>
          </DesignCard>
        </div>
      </Panel>

      <Panel v-else-if="tab === 'market'" :title="$t('designs.market')">
        <template #actions>
          <button class="btn sm ghost icon" :aria-label="$t('designs.refresh')" @click="loadCat(true)"><Icon name="refresh" /></button>
        </template>
        <Skeleton v-if="!cat" kind="cards" :n="2" />
        <template v-else>
          <input v-if="cat.length > 6" v-model="catQ" class="catq" :placeholder="$t('designs.search')">
          <p v-if="!catShown.length" class="empty-state">{{ $t('designs.marketEmpty') }}</p>
          <div class="cards">
            <DesignCard v-for="d in catShown" :key="d.slug" :name="d.name" :tokens="d.tokens" :sub="sub($t('designs.by', { name: d.author }), skinLine(d.skin))">
              <button class="btn sm primary" :disabled="!!draft" @click="add(d)">{{ $t('designs.add') }}</button>
            </DesignCard>
          </div>
        </template>
      </Panel>

      <Panel v-else :title="$t('designs.shared')">
        <p v-if="!data.gallery.length" class="empty-state">{{ $t('designs.galleryEmpty') }}</p>
        <div class="cards">
          <DesignCard v-for="d in data.gallery" :key="d.id" :name="d.name" :tokens="d.tokens" :active="data.pick === `d:${d.id}`" :sub="sub($t('designs.by', { name: d.author }), usersLine(d), skinLine(d.skin))">
            <button v-if="data.pick !== `d:${d.id}`" class="btn sm primary" :disabled="!!draft" @click="use(`d:${d.id}`)">{{ $t('designs.use') }}</button>
            <button class="btn sm" :disabled="!!draft" @click="startEdit(undefined, lookOf(d), $t('designs.copyName', { name: d.name }))">{{ $t('designs.copy') }}</button>
            <button class="btn sm ghost" @click="copyCode(d)">{{ $t('designs.code') }}</button>
            <button v-if="isOwner" class="btn sm ghost sure" :class="{ danger: armed === `del${d.id}` }" @click="remove(d)">{{ armed === `del${d.id}` ? $t('designs.sure') : $t('designs.delete') }}</button>
          </DesignCard>
        </div>
      </Panel>
      </div>
      <p class="faint small">{{ $t('designs.safe') }}</p>
    </div>
  </div>
</template>

<style scoped>
.stack { display: flex; flex-direction: column; gap: 14px; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; }
.ed { display: flex; flex-direction: column; gap: 12px; }
.fld { display: flex; flex-direction: column; gap: 4px; }
.row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.rad { display: flex; align-items: center; gap: 8px; }
.colors { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px; }
.col { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.col input { width: 36px; height: 32px; padding: 0; border: 1px solid var(--line-2); border-radius: var(--radius-sm); background: none; cursor: pointer; }
textarea { width: 100%; resize: vertical; }
.css { font-size: 12px; }
.thumb { width: 40px; height: 40px; object-fit: cover; border-radius: var(--radius-sm); border: 1px solid var(--line-2); }
.where { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }
.imp { margin-bottom: 10px; }
.imp input { flex: 1; min-width: 0; }
.catq { width: 100%; margin-bottom: 10px; }
.ed > .chip { align-self: flex-start; }
</style>
