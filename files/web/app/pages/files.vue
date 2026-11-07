<script setup lang="ts">
/** file browser over the roots in /etc/dash/files.json: ?r=<root>&p=<path> (a file path opens its folder + preview) */
useHead({ title: 'Files · Bastion' })
const { t } = useI18n()
const route = useRoute()
const { run } = useActions()
const { armed, arm } = useArm()
const { toast } = useToast()
const enc = encodeURIComponent

const tab = usePageTab('browse')
const tabs = computed(() => [
  { key: 'browse', label: t('files.tabs.browse'), icon: 'folder' },
  { key: 'shared', label: t('files.tabs.shared'), icon: 'link', badge: shares.value?.shares?.filter((s: any) => !s.expired).length || undefined },
  { key: 'bookmarks', label: t('files.tabs.bookmarks'), icon: 'bookmark' },
])

const { data: rootsData, refresh: refreshRoots } = useFetch<any>('/api/files/roots', { server: false })
const roots = computed<any[]>(() => rootsData.value?.roots ?? [])
const rootId = computed(() => (typeof route.query.r === 'string' && route.query.r) || 'files')
const relPath = computed(() => (typeof route.query.p === 'string' ? route.query.p : ''))
const root = computed(() => roots.value.find(r => r.id === rootId.value))
const hostRoots = computed(() => roots.value.filter(r => !r.ct))
const ctRoots = computed(() => roots.value.filter(r => r.ct))
const inCt = computed(() => !!root.value?.ct)

// --- browse ---
const picked = ref<string[]>([])
const dir = ref<any>(null)
const dirPath = ref('')
const file = ref<any>(null) // the open preview
const err = ref('')
const busy = ref(false)

function go(r: string, p: string, replace = false) {
  return navigateTo({ query: { ...route.query, r: r === 'files' ? undefined : r, p: p || undefined }, hash: '' }, { replace })
}
const join = (a: string, b: string) => (a ? `${a}/${b}` : b)
const parentOf = (p: string) => p.split('/').slice(0, -1).join('/')

async function load() {
  picked.value = []
  err.value = ''
  busy.value = true
  try {
    let d = relPath.value
    file.value = null
    if (d) {
      const st = await $fetch<any>('/api/files/stat', { query: { root: rootId.value, p: d } })
      if (!st.dir) { d = parentOf(d); file.value = { ...st, p: relPath.value }; textBody.value = ''; shareUrl.value = ''; renaming.value = false }
    }
    dir.value = await $fetch<any>('/api/files/list', { query: { root: rootId.value, p: d } })
    if (d === '~') { go(rootId.value, dir.value.path, true); return } // a container's home: show its real path
    dirPath.value = d
    if (file.value) loadText()
  } catch (e: any) { err.value = e?.data?.statusMessage || e?.message || 'failed' } finally { busy.value = false }
}
const sq = ref('')
watch(() => [route.query.r, route.query.p], () => { sq.value = ''; load() }, { immediate: true })

// --- search (fuzzy names below the open folder) ---
const found = ref<{ results: any[], cut: boolean, total: number } | null>(null)
const searching = ref(false)
let stimer: any
let sseq = 0
watch(sq, (v) => {
  clearTimeout(stimer)
  if (!v.trim()) { found.value = null; searching.value = false; sseq++; return }
  searching.value = true
  stimer = setTimeout(async () => {
    const my = ++sseq
    try {
      const r = await $fetch<any>('/api/files/search', { query: { root: rootId.value, p: dirPath.value, q: v } })
      if (my === sseq) found.value = r
    } catch (e: any) {
      if (my === sseq) { found.value = { results: [], cut: false, total: 0 }; toast(e?.data?.statusMessage || e?.message || 'failed', { tone: 'bad' }) }
    } finally { if (my === sseq) searching.value = false }
  }, 350)
})
const shown = computed<any[]>(() => found.value?.results ?? dir.value?.entries ?? [])

const pth = (e: any) => e.p ?? join(dirPath.value, e.name)
const open = (e: any) => go(rootId.value, pth(e))
const closePreview = () => go(rootId.value, dirPath.value)

const rawUrl = (p: string, dl = false) => `/api/files/raw?root=${enc(rootId.value)}&p=${enc(p)}${dl ? '&dl=1' : ''}`
const kind = (m: string, name: string) => {
  if (m.startsWith('video/')) return 'video'
  if (m.startsWith('audio/')) return 'audio'
  if (m.startsWith('image/')) return 'image'
  if (m === 'application/pdf') return 'pdf'
  if (m.startsWith('text/') || /\.(md|json|ya?ml|toml|ini|conf|log|sh|py|ts|js|vue|csv|env|xml|yml)$/i.test(name) || ['application/json', 'application/xml', 'application/javascript'].includes(m)) return 'text'
  return 'other'
}
const fileKind = computed(() => (file.value ? kind(file.value.mime, file.value.name) : ''))
const icon = (e: any) => (e.dir ? 'folder' : kind(e.mime, e.name) === 'image' ? 'image' : 'file-text')

const textBody = ref('')
const textCut = ref(false)
async function loadText() {
  if (fileKind.value !== 'text') return
  try {
    const body = await $fetch<string>(rawUrl(file.value.p), { headers: { Range: 'bytes=0-204799' }, responseType: 'text' })
    textBody.value = body
    textCut.value = file.value.size > 204800
  } catch (e: any) { textBody.value = e?.data?.statusMessage || e?.message || 'failed' }
}

// --- actions on the open file ---
const renaming = ref(false)
const newName = ref('')
function startRename() { newName.value = file.value.name; renaming.value = true }
function doRename() {
  const p = file.value.p
  const name = newName.value.trim()
  if (!name || name === file.value.name) { renaming.value = false; return }
  run('files_rename', { root: rootId.value, p, name }, () => go(rootId.value, join(parentOf(p), name), true))
  renaming.value = false
}
function togglePick(name: string) {
  picked.value = picked.value.includes(name) ? picked.value.filter(n => n !== name) : [...picked.value, name]
}
function selAll() {
  picked.value = picked.value.length === dir.value?.entries.length ? [] : (dir.value?.entries.map((e: any) => e.name) ?? [])
}
function thumb(e: any) {
  return !inCt.value && !e.dir && String(e.mime || '').startsWith('image/') && e.size < 6e6
    ? `/api/files/raw?root=${encodeURIComponent(rootId.value)}&p=${encodeURIComponent(pth(e))}` : ''
}
function delRow(e: any) {
  if (!arm('row:' + e.name)) return
  run('files_delete', { root: rootId.value, p: join(dirPath.value, e.name) }, () => load())
}
function delPicked() {
  if (!arm('bulk')) return
  const ps = picked.value.map(n => join(dirPath.value, n))
  run('files_delete', { root: rootId.value, p: ps }, () => { picked.value = []; load() })
}
function del(p: string, name: string) {
  if (!arm(p)) return
  run('files_delete', { root: rootId.value, p }, () => { if (file.value) closePreview(); else load() })
}

const ttl = ref(72)
const shareUrl = ref('')
const copied = ref('')
const { data: shares, refresh: refreshShares } = useFetch<any>('/api/files/shares', { server: false })
async function doShare() {
  try {
    const r = await $fetch<any>('/api/files/share', { method: 'POST', body: { root: rootId.value, p: file.value.p, ttl_hours: ttl.value } })
    await refreshShares()
    shareUrl.value = `${shares.value?.base}/f/${r.token}`
  } catch (e: any) { toast(e?.data?.statusMessage || e?.message || 'failed', { tone: 'bad' }) }
}
function copy(url: string, id: string) {
  navigator.clipboard?.writeText(url)
  copied.value = id
  setTimeout(() => copied.value === id && (copied.value = ''), 1500)
}
async function revoke(tok: string) {
  await $fetch('/api/files/share', { method: 'POST', body: { revoke: tok } }).catch((e: any) => toast(e?.data?.statusMessage || e?.message || 'failed', { tone: 'bad' }))
  refreshShares()
}
const when = (ts: number) => fmtDate(ts * 1000, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

// --- new folder ---
const mk = ref(false)
const mkName = ref('')
async function doMkdir() {
  const name = mkName.value.trim()
  if (!name) return
  try {
    await $fetch('/api/files/mkdir', { method: 'POST', body: { root: rootId.value, p: dirPath.value, name } })
    mk.value = false
    mkName.value = ''
    load()
  } catch (e: any) { toast(e?.data?.statusMessage || e?.message || 'failed', { tone: 'bad' }) }
}

// --- upload (8 MB chunks) ---
const picker = ref<HTMLInputElement>()
const ups = ref<{ name: string, done: number, total: number, state: string }[]>([])
const CH = 8 * 2 ** 20
async function upload(files: FileList | null) {
  if (!files?.length) return
  const target = { root: rootId.value, p: dirPath.value }
  const items = [...files].map(f => reactive({ name: f.name, done: 0, total: f.size, state: 'run' }))
  ups.value = items
  await Promise.all([...files].map(async (f, i) => {
    const it = items[i]!
    try {
      let off = 0
      let id = ''
      do {
        const end = Math.min(off + CH, f.size)
        const q = new URLSearchParams({ ...target, name: f.name, offset: String(off), final: end >= f.size ? '1' : '0', id })
        const res = await $fetch<{ id?: string }>(`/api/files/upload?${q}`, { method: 'POST', body: f.slice(off, end), headers: { 'Content-Type': 'application/octet-stream' } })
        if (res?.id) id = res.id
        off = end
        it.done = off
      } while (off < f.size)
      it.state = 'done'
    } catch (e: any) { it.state = 'failed'; toast(`${f.name}: ${e?.data?.statusMessage || e?.message || 'failed'}`, { tone: 'bad' }) }
  }))
  if (picker.value) picker.value.value = ''
  load()
  setTimeout(() => (ups.value = ups.value.filter(u => u.state === 'failed')), 3000)
}

// --- bookmarks ---
const bm = reactive({ label: '', path: '', writable: false })
async function addBm() {
  try {
    await $fetch('/api/files/bookmarks', { method: 'POST', body: { ...bm } })
    Object.assign(bm, { label: '', path: '', writable: false })
    refreshRoots()
  } catch (e: any) { toast(e?.data?.statusMessage || e?.message || 'failed', { tone: 'bad' }) }
}
async function rmBm(id: string) {
  if (!arm(`bm:${id}`)) return
  await $fetch('/api/files/bookmarks', { method: 'POST', body: { id } }).catch((e: any) => toast(e?.data?.statusMessage || e?.message || 'failed', { tone: 'bad' }))
  refreshRoots()
}
const pickRoot = (id: string) => { tab.value = 'browse'; nextTick(() => go(id, '')) }
</script>

<template>
  <div>
    <h2 class="sec">{{ $t('files.title') }}</h2>
    <PageTabs v-model="tab" :tabs="tabs" />

    <template v-if="tab === 'browse'">
      <div class="chips">
        <button v-for="r in hostRoots" :key="r.id" class="chip" :class="{ on: r.id === rootId }" @click="go(r.id, '')">{{ r.label }}</button>
        <select v-if="ctRoots.length" class="ctsel" :class="{ on: inCt }" :value="inCt ? rootId : ''" :aria-label="$t('files.containers')" @change="go(($event.target as HTMLSelectElement).value, '~')">
          <option value="" disabled>{{ $t('files.containers') }}</option>
          <option v-for="r in ctRoots" :key="r.id" :value="r.id">{{ r.label }}{{ r.running ? '' : ' · ' + $t('files.stopped') }}</option>
        </select>
      </div>
      <div v-if="dir" class="bar">
        <nav class="crumbs">
          <template v-for="(c, i) in dir.parents" :key="c.p">
            <Icon v-if="i" name="chevron-right" :size="12" class="faint" />
            <button class="lnk" @click="go(rootId, c.p)">{{ c.name }}</button>
          </template>
        </nav>
        <div class="tools">
          <template v-if="dir.writable">
            <button class="btn sm" @click="picker?.click()"><Icon name="cloud-upload" :size="14" /> {{ $t('files.upload') }}</button>
            <button class="btn sm" @click="mk = !mk"><Icon name="plus" :size="14" /> {{ $t('files.newFolder') }}</button>
          </template>
          <button class="btn sm ghost" :disabled="busy" @click="load"><Icon name="refresh-cw" :size="14" /> {{ $t('files.refresh') }}</button>
          <span v-if="!dir.writable" class="pill">{{ $t('files.readOnly') }}</span>
        </div>
        <div class="search">
          <Icon name="search" :size="14" class="faint" />
          <input v-model="sq" type="search" :placeholder="$t('files.search')" :aria-label="$t('files.search')" autocomplete="off" autocapitalize="off" spellcheck="false">
          <span v-if="searching" class="small faint">{{ $t('files.searching') }}</span>
        </div>
        <input ref="picker" type="file" multiple hidden @change="upload(($event.target as HTMLInputElement).files)">
        <form v-if="mk" class="row-form" @submit.prevent="doMkdir">
          <input v-model="mkName" :placeholder="$t('files.folderName')" autofocus>
          <button class="btn primary sm" type="submit">{{ $t('files.create') }}</button>
        </form>
      </div>

      <div v-for="u in ups" :key="u.name" class="up">
        <div class="small up-name">{{ u.name }} <span class="faint">{{ u.state === 'run' ? Math.round(100 * u.done / Math.max(u.total, 1)) + '%' : u.state === 'done' ? $t('files.done') : $t('files.failed') }}</span></div>
        <div class="track"><div class="fill" :class="{ bad: u.state === 'failed' }" :style="{ transform: `scaleX(${u.done / Math.max(u.total, 1)})` }" /></div>
      </div>

      <div v-if="err" class="errbox">{{ err }}</div>
      <Skeleton v-else-if="!dir" kind="rows" />
      <Panel v-else :title="root?.label || rootId">
        <div v-if="!shown.length && !searching" class="empty-state">{{ found ? $t('files.noMatch') : $t('files.empty') }}</div>
        <div v-if="found?.cut" class="small faint">{{ $t('files.searchCut') }}</div>
        <div v-if="dir.writable && dir.entries.length && !found" class="bulk">
          <template v-if="armed === 'bulk'">
            <span class="confirm-t">{{ $t('files.deleteAsk', { n: picked.length }) }}</span>
            <span class="confirm-b">
              <button class="btn sm" @click="armed = ''">{{ $t('files.cancel') }}</button>
              <button class="btn sm danger" @click="delPicked">{{ $t('files.delete') }}</button>
            </span>
          </template>
          <template v-else>
            <button class="lnk small" @click="selAll">{{ picked.length === dir.entries.length ? $t('files.clear') : $t('files.selectAll') }}</button>
            <button v-if="picked.length" class="btn sm danger" @click="delPicked">{{ $t('files.deleteN', { n: picked.length }) }}</button>
          </template>
        </div>
        <div v-for="e in shown" :key="e.p ?? e.name" class="frow" :class="{ sel: !found && picked.includes(e.name), asking: !found && armed === 'row:' + e.name }">
          <template v-if="!found && armed === 'row:' + e.name">
            <span class="confirm-t">{{ $t('files.deleteAskOne', { name: e.name }) }}</span>
            <span class="confirm-b">
              <button class="btn sm" @click="armed = ''">{{ $t('files.cancel') }}</button>
              <button class="btn sm danger" @click="delRow(e)">{{ $t('files.delete') }}</button>
            </span>
          </template>
          <template v-else>
            <input v-if="dir.writable && !found" type="checkbox" class="pick" :checked="picked.includes(e.name)" :aria-label="$t('files.select')" @change="togglePick(e.name)">
            <button class="frow-main" @click="open(e)">
              <span class="ftile" :class="{ dirc: e.dir }">
                <img v-if="thumb(e)" :src="thumb(e)" alt="" loading="lazy">
                <Icon v-else :name="icon(e)" :size="18" />
              </span>
              <span class="ftext">
                <span class="fname">{{ e.name }}</span>
                <span class="fmeta small faint"><template v-if="found && e.in">{{ e.in }} · </template><template v-if="!e.dir">{{ bytes(e.size) }} · </template>{{ fmtDate(e.mtime * 1000) }}</span>
              </span>
              <Icon v-if="e.dir" name="chevron-right" :size="14" class="faint go" />
            </button>
            <button v-if="dir.writable && !found" class="btn sm ghost icon trash" :aria-label="$t('files.delete')" @click="delRow(e)">
              <Icon name="trash-2" :size="14" />
            </button>
          </template>
        </div>
      </Panel>
    </template>

    <template v-else-if="tab === 'shared'">
      <div v-if="shares && shares.funnel === false" class="small warn">{{ $t('files.publicOff') }}</div>
      <Skeleton v-if="!shares" kind="rows" />
      <div v-else-if="!shares.shares.length" class="empty-state">{{ $t('files.noShares') }}</div>
      <Panel v-else :title="$t('files.tabs.shared')">
        <div v-for="s in shares.shares" :key="s.token" class="srow">
          <div class="sinfo">
            <div class="fname">{{ s.name }}</div>
            <div class="small faint mono">{{ s.root }}/{{ s.p }}</div>
            <div class="small" :class="s.expired ? 'bad-t' : 'muted'">{{ s.expired ? $t('files.expired') : $t('files.expires', { when: when(s.expires) }) }}</div>
          </div>
          <div class="sbtns">
            <button v-if="!s.expired" class="btn sm" @click="copy(s.url, s.token)">{{ copied === s.token ? $t('files.copied') : $t('files.copy') }}</button>
            <button class="btn sm danger" @click="revoke(s.token)">{{ $t('files.revoke') }}</button>
          </div>
        </div>
      </Panel>
    </template>

    <template v-else>
      <Panel :title="$t('files.tabs.bookmarks')">
        <div v-for="r in hostRoots" :key="r.id" class="srow">
          <div class="sinfo">
            <button class="lnk fname" @click="pickRoot(r.id)">{{ r.label }}</button>
            <div class="small faint mono">{{ r.path }}</div>
          </div>
          <div class="sbtns">
            <span class="pill" :class="r.writable ? 'warn' : ''">{{ r.writable ? $t('files.writable') : $t('files.readOnly') }}</span>
            <span v-if="r.id === 'files'" class="small faint">{{ $t('files.locked') }}</span>
            <button v-else class="btn sm danger" :class="{ on: armed === `bm:${r.id}` }" @click="rmBm(r.id)">{{ armed === `bm:${r.id}` ? $t('files.deleteSure') : $t('files.remove') }}</button>
          </div>
        </div>
      </Panel>
      <Panel :title="$t('files.bmAdd')">
        <form class="col-form" @submit.prevent="addBm">
          <input v-model="bm.label" :placeholder="$t('files.bmLabel')">
          <input v-model="bm.path" class="mono" :placeholder="$t('files.bmPath')">
          <label class="small"><input v-model="bm.writable" type="checkbox"> {{ $t('files.bmWritable') }}</label>
          <button class="btn primary" type="submit" :disabled="!bm.label || !bm.path">{{ $t('files.bmAdd') }}</button>
        </form>
      </Panel>
    </template>

    <Teleport to="body">
      <Transition name="sheet">
      <div v-if="file && tab === 'browse'" class="scrim" @click.self="closePreview">
        <div class="sheet">
          <header class="shead">
            <div class="fname">{{ file.name }}</div>
            <button class="btn ghost icon" :aria-label="$t('files.close')" @click="closePreview"><Icon name="x" :size="18" /></button>
          </header>
          <div class="body">
            <video v-if="fileKind === 'video'" :src="rawUrl(file.p)" controls playsinline preload="metadata" />
            <audio v-else-if="fileKind === 'audio'" :src="rawUrl(file.p)" controls preload="metadata" />
            <img v-else-if="fileKind === 'image'" :src="rawUrl(file.p)" alt="">
            <iframe v-else-if="fileKind === 'pdf'" :src="rawUrl(file.p)" />
            <template v-else-if="fileKind === 'text'">
              <pre class="code">{{ textBody }}</pre>
              <div v-if="textCut" class="small faint">{{ $t('files.truncated') }}</div>
            </template>
            <div v-else class="muted small">{{ $t('files.noPreview') }}</div>
          </div>
          <div class="small muted info">{{ bytes(file.size) }} · {{ file.mime }} · {{ fmtDate(file.mtime * 1000) }}</div>
          <div class="btns">
            <a class="btn" :href="rawUrl(file.p, true)" download>{{ $t('files.download') }}</a>
            <button v-if="dir?.writable && !inCt" class="btn" @click="doShare">{{ $t('files.share') }}</button>
            <template v-if="dir?.writable">
              <button class="btn" @click="startRename">{{ $t('files.rename') }}</button>
              <button class="btn danger" :class="{ on: armed === file.p }" @click="del(file.p, file.name)">{{ armed === file.p ? $t('files.deleteSure') : $t('files.delete') }}</button>
            </template>
          </div>
          <form v-if="renaming" class="row-form" @submit.prevent="doRename">
            <input v-model="newName" :placeholder="$t('files.newName')">
            <button class="btn primary sm" type="submit">{{ $t('files.save') }}</button>
            <button class="btn ghost sm" type="button" @click="renaming = false">{{ $t('files.cancel') }}</button>
          </form>
          <div v-if="!inCt" class="row-form">
            <label class="small muted">{{ $t('files.shareFor') }}</label>
            <select v-model.number="ttl">
              <option :value="24">{{ $t('files.hours', { n: 24 }) }}</option>
              <option :value="72">{{ $t('files.days', { n: 3 }) }}</option>
              <option :value="168">{{ $t('files.days', { n: 7 }) }}</option>
              <option :value="720">{{ $t('files.days', { n: 30 }) }}</option>
              <option :value="2160">{{ $t('files.days', { n: 90 }) }}</option>
            </select>
          </div>
          <div v-if="shareUrl" class="row-form">
            <input :value="shareUrl" readonly class="mono" @focus="($event.target as HTMLInputElement).select()">
            <button class="btn sm" @click="copy(shareUrl, 'new')">{{ copied === 'new' ? $t('files.copied') : $t('files.copy') }}</button>
          </div>
        </div>
      </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.ctsel { flex: none; width: auto; min-height: 0; padding: 4px 10px; border-radius: 999px; }
.ctsel.on { border-color: var(--accent); }
.search { display: flex; align-items: center; gap: 8px; padding: 0 10px; background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius-sm); }
.search input { flex: 1; min-width: 0; border: 0; background: none; padding: 8px 0; outline: none; }
.chips { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 10px; }
.bar { display: flex; flex-direction: column; gap: 8px; margin-bottom: 10px; }
.crumbs { display: flex; flex-wrap: wrap; align-items: center; gap: 2px; padding: 6px 10px; background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius-sm); }
.tools { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.row-form { display: flex; gap: 6px; align-items: center; margin-top: 8px; }
.row-form input, .row-form select { flex: 1; min-width: 0; }
.col-form { display: flex; flex-direction: column; gap: 8px; }
.frow { display: flex; align-items: center; gap: 6px; padding: 2px 4px; border-radius: var(--radius-sm); transition: background .12s; }
.frow + .frow { margin-top: 2px; }
.frow:hover, .frow.sel { background: var(--panel-2); }
.frow.sel { box-shadow: inset 0 0 0 1px var(--accent); }
.frow-main { display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0; background: none; border: 0; color: var(--text); font: inherit; text-align: left; cursor: pointer; padding: 6px 4px; min-height: 52px; }
.ftile { width: 38px; height: 38px; flex: none; display: grid; place-items: center; border-radius: var(--radius-sm); background: var(--panel-2); color: var(--muted); overflow: hidden; }
.frow:hover .ftile { background: var(--bg); }
.ftile.dirc { background: var(--accent-soft); color: var(--accent); }
.ftile img { width: 100%; height: 100%; object-fit: cover; }
.ftext { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.fname { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
.fmeta { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.go { flex: none; }
.frow.asking { padding: 8px 10px; gap: 10px; background: var(--bad-soft); min-height: 52px; }
.confirm-t { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
.confirm-b { display: flex; gap: 8px; flex: none; }
.bulk .confirm-t { white-space: normal; }
.trash { flex: none; margin-right: 4px; }
.pick { width: 18px; height: 18px; flex: none; margin: 0 2px 0 6px; accent-color: var(--accent); }
.bulk { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid var(--line); }
@media (pointer: coarse) { .frow .btn.icon { min-width: 40px; min-height: 40px; } }
.up { margin-bottom: 8px; }
.up-name { overflow-wrap: anywhere; }
.track { height: 6px; background: var(--track); border-radius: 3px; overflow: hidden; }
.fill { width: 100%; height: 100%; background: var(--accent); transform-origin: left; transition: transform var(--dur) var(--ease-out); }
.fill.bad { background: var(--bad); }
.srow { display: flex; gap: 10px; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--line); flex-wrap: wrap; }
.srow:last-child { border-bottom: 0; }
.sinfo { flex: 1; min-width: 180px; }
.sbtns { display: flex; gap: 6px; align-items: center; }
.bad-t { color: var(--bad); }
.scrim { position: fixed; inset: 0; z-index: 60; background: rgba(0, 0, 0, .6); display: flex; align-items: flex-end; justify-content: center; }
.sheet { background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius) var(--radius) 0 0; width: 100%; max-width: 760px; max-height: 92vh; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 10px; }
@media (min-width: 641px) { .scrim { align-items: center; } .sheet { border-radius: var(--radius); } }
.shead { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.body video, .body img, .body iframe { width: 100%; max-height: 62vh; border: 0; border-radius: var(--radius-sm); background: var(--bg); object-fit: contain; }
.body iframe { height: 62vh; }
.body audio { width: 100%; }
.code { margin: 0; max-height: 50vh; overflow: auto; background: var(--bg); border-radius: var(--radius-sm); padding: 8px; font-size: 12px; white-space: pre-wrap; overflow-wrap: anywhere; }
.btns { display: flex; flex-wrap: wrap; gap: 6px; }
</style>
