<script setup lang="ts">
const { t } = useI18n()
useHead({ title: () => `${t('designs.title')} · pve` })
const { toast } = useToast()
const { armed, arm } = useArm()

type Design = { id: number, uid: number, author: string, name: string, tokens: DesignTokens, shared: boolean, users: number }
type Data = { mine: Design[], gallery: Design[], presets: { key: string, name: string, tokens: DesignTokens }[], pick: string }
const data = ref<Data | null>(null)
const err = ref('')
const why = (e: any) => e?.data?.statusMessage || e?.statusMessage || e?.message || 'failed'

async function load() {
  try { data.value = await $fetch<Data>('/api/designs'); err.value = '' } catch (e) { err.value = why(e) }
}
onMounted(load)

const tokensOf = (pick: string) => {
  const d = data.value
  if (!d) return null
  if (pick.startsWith('p:')) return pick === 'p:default' ? null : d.presets.find(p => `p:${p.key}` === pick)?.tokens ?? null
  return [...d.mine, ...d.gallery].find(x => `d:${x.id}` === pick)?.tokens ?? null
}

async function use(pick: string) {
  if (!data.value || draft.value) return
  const before = data.value.pick
  data.value.pick = pick
  applyDesign(tokensOf(pick))
  try { applyDesign((await $fetch<any>('/api/designs/pick', { method: 'POST', body: { pick } })).tokens); load() } catch (e) {
    data.value.pick = before
    applyDesign(tokensOf(before))
    toast(why(e), { tone: 'bad' })
  }
}

// the editor: changes paint the whole app live, Cancel puts the design in use back
const draft = ref<{ id?: number, name: string, tokens: DesignTokens, shared: boolean } | null>(null)
const saving = ref(false)
function startEdit(d?: Design, from?: DesignTokens, name?: string) {
  const base = d?.tokens ?? from ?? tokensOf(data.value?.pick ?? 'p:default') ?? data.value!.presets[0]!.tokens
  draft.value = { id: d?.id, name: d?.name ?? name ?? t('designs.new'), tokens: { ...base }, shared: d?.shared ?? false }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
watch(() => draft.value?.tokens, (tk) => { if (tk) applyDesign(tk, false) }, { deep: true })
function cancel() {
  draft.value = null
  applyDesign(tokensOf(data.value?.pick ?? 'p:default'))
}
async function save() {
  if (!draft.value) return
  saving.value = true
  try {
    const d = await $fetch<Design>('/api/designs', { method: 'POST', body: draft.value })
    draft.value = null
    await load()
    // a new design is what you were looking at, so it becomes the one in use
    await use(data.value?.pick === `d:${d.id}` ? data.value.pick : `d:${d.id}`)
    toast(t('designs.saved'), { tone: 'ok' })
  } catch (e) { toast(why(e), { tone: 'bad' }) } finally { saving.value = false }
}

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
    applyDesign(tokensOf(data.value?.pick ?? 'p:default'))
  } catch (e) { toast(why(e), { tone: 'bad' }) }
}

async function copyCode(d: { name: string, tokens: DesignTokens }) {
  try { await navigator.clipboard.writeText(designCode(d.name, d.tokens)); toast(t('designs.codeCopied'), { tone: 'ok' }) } catch (e) { toast(why(e), { tone: 'bad' }) }
}

const importing = ref(false)
const code = ref('')
function doImport() {
  const d = readDesignCode(code.value)
  if (!d) return toast(t('designs.badCode'), { tone: 'bad' })
  importing.value = false
  code.value = ''
  startEdit(undefined, d.tokens, d.name)
}

const usersLine = (d: Design) => t('designs.users', d.users)
const isOwner = computed(() => useAddons().role.value === 'owner')

// the marketplace catalogue (designs published to GitHub from any install); Add = a copy in your designs, in use at once
const cat = ref<{ slug: string, name: string, author: string, tokens: DesignTokens }[] | null>(null)
const catQ = ref('')
async function loadCat(fresh = false) {
  try { cat.value = (await $fetch<any>(`/api/designs/catalogue${fresh ? '?fresh=1' : ''}`)).designs } catch { cat.value ??= [] }
}
onMounted(() => loadCat())
const catShown = computed(() => {
  const q = catQ.value.trim().toLowerCase()
  return (cat.value ?? []).filter(d => !q || `${d.name} ${d.author}`.toLowerCase().includes(q))
})
async function add(d: { name: string, tokens: DesignTokens }) {
  try {
    const n = await $fetch<Design>('/api/designs', { method: 'POST', body: { name: d.name, tokens: d.tokens } })
    await load()
    await use(`d:${n.id}`)
    toast(t('designs.added'), { tone: 'ok' })
  } catch (e) { toast(why(e), { tone: 'bad' }) }
}
const publish = (d: Design) => useConfirm().ask('design_publish', { id: d.id, name: d.name }, t('designs.publishLabel', { name: d.name }))
</script>

<template>
  <div>
    <h2 class="sec">{{ $t('designs.title') }}</h2>
    <div v-if="err" class="errbox">{{ err }}</div>
    <Skeleton v-else-if="!data" kind="cards" :n="4" />
    <template v-else>
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
          <div class="faint small">{{ $t('designs.colors') }}</div>
          <div class="colors">
            <label v-for="k in DESIGN_COLORS" :key="k" class="col">
              <input v-model="draft.tokens[k]" type="color">
              <span class="small">{{ $t(`designs.c.${k}`) }}</span>
            </label>
          </div>
          <button class="chip" :class="{ on: draft.shared }" @click="draft.shared = !draft.shared">{{ $t('designs.share') }}</button>
          <div class="row">
            <button class="btn primary" :disabled="saving || !draft.name.trim()" @click="save">{{ $t('designs.save') }}</button>
            <button class="btn ghost" @click="cancel">{{ $t('designs.cancel') }}</button>
          </div>
        </div>
      </Panel>

      <Panel :title="$t('designs.yours')">
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
          <DesignCard v-for="d in data.mine" :key="d.id" :name="d.name" :tokens="d.tokens" :active="data.pick === `d:${d.id}`" :sub="d.shared ? `${$t('designs.sharedPill')} · ${usersLine(d)}` : ''">
            <button v-if="data.pick !== `d:${d.id}`" class="btn sm primary" :disabled="!!draft" @click="use(`d:${d.id}`)">{{ $t('designs.use') }}</button>
            <button class="btn sm" :disabled="!!draft" @click="startEdit(d)">{{ $t('designs.edit') }}</button>
            <button class="chip" :class="{ on: d.shared }" @click="share(d)">{{ $t('designs.sharedPill') }}</button>
            <button class="btn sm ghost" @click="copyCode(d)">{{ $t('designs.code') }}</button>
            <button v-if="isOwner" class="btn sm ghost" @click="publish(d)">{{ $t('designs.publish') }}</button>
            <button class="btn sm ghost sure" :class="{ danger: armed === `del${d.id}` }" @click="remove(d)">{{ armed === `del${d.id}` ? $t('designs.sure') : $t('designs.delete') }}</button>
          </DesignCard>
        </div>
      </Panel>

      <Panel :title="$t('designs.market')">
        <template #actions>
          <button class="btn sm ghost icon" :aria-label="$t('designs.refresh')" @click="loadCat(true)"><Icon name="refresh" /></button>
        </template>
        <Skeleton v-if="!cat" kind="cards" :n="2" />
        <template v-else>
          <input v-if="cat.length > 6" v-model="catQ" class="catq" :placeholder="$t('designs.search')">
          <p v-if="!catShown.length" class="empty-state">{{ $t('designs.marketEmpty') }}</p>
          <div class="cards">
            <DesignCard v-for="d in catShown" :key="d.slug" :name="d.name" :tokens="d.tokens" :sub="$t('designs.by', { name: d.author })">
              <button class="btn sm primary" :disabled="!!draft" @click="add(d)">{{ $t('designs.add') }}</button>
            </DesignCard>
          </div>
        </template>
      </Panel>

      <Panel :title="$t('designs.shared')">
        <p v-if="!data.gallery.length" class="empty-state">{{ $t('designs.galleryEmpty') }}</p>
        <div class="cards">
          <DesignCard v-for="d in data.gallery" :key="d.id" :name="d.name" :tokens="d.tokens" :active="data.pick === `d:${d.id}`" :sub="`${$t('designs.by', { name: d.author })} · ${usersLine(d)}`">
            <button v-if="data.pick !== `d:${d.id}`" class="btn sm primary" :disabled="!!draft" @click="use(`d:${d.id}`)">{{ $t('designs.use') }}</button>
            <button class="btn sm" :disabled="!!draft" @click="startEdit(undefined, d.tokens, $t('designs.copyName', { name: d.name }))">{{ $t('designs.copy') }}</button>
            <button class="btn sm ghost" @click="copyCode(d)">{{ $t('designs.code') }}</button>
            <button v-if="isOwner" class="btn sm ghost sure" :class="{ danger: armed === `del${d.id}` }" @click="remove(d)">{{ armed === `del${d.id}` ? $t('designs.sure') : $t('designs.delete') }}</button>
          </DesignCard>
        </div>
      </Panel>

      <Panel :title="$t('designs.builtin')">
        <div class="cards">
          <DesignCard v-for="p in data.presets" :key="p.key" :name="p.name" :tokens="p.tokens" :active="data.pick === `p:${p.key}`">
            <button v-if="data.pick !== `p:${p.key}`" class="btn sm primary" :disabled="!!draft" @click="use(`p:${p.key}`)">{{ $t('designs.use') }}</button>
            <button class="btn sm" :disabled="!!draft" @click="startEdit(undefined, p.tokens, $t('designs.copyName', { name: p.name }))">{{ $t('designs.copy') }}</button>
          </DesignCard>
        </div>
      </Panel>
    </template>
  </div>
</template>

<style scoped>
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; }
.ed { display: flex; flex-direction: column; gap: 12px; }
.fld { display: flex; flex-direction: column; gap: 4px; }
.row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.rad { display: flex; align-items: center; gap: 8px; }
.colors { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px; }
.col { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.col input { width: 36px; height: 32px; padding: 0; border: 1px solid var(--line-2); border-radius: var(--radius-sm); background: none; cursor: pointer; }
.imp { margin-bottom: 10px; }
.catq { width: 100%; margin-bottom: 10px; }
.imp input { flex: 1; min-width: 0; }
.ed > .chip { align-self: flex-start; }
</style>
