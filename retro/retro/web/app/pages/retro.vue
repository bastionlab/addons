<script setup lang="ts">
/** retro games: the library (filter by console + name, tap = play in the browser), free homebrew to add, own files */
useHead({ title: 'Retro · Bastion' })
const { t } = useI18n()
const { data: lib, error, refresh } = useShared<any>('retro', '/api/retro')
usePoll(refresh, 30000)
const { ip } = useDashConfig()
const { run } = useActions()
const { armed, arm } = useArm()
const { toast } = useToast()

const tab = usePageTab('library')
const tabs = computed(() => [
  { key: 'library', label: t('retro.tabs.library'), icon: 'gamepad', badge: lib.value?.games?.length || undefined },
  { key: 'get', label: t('retro.tabs.get'), icon: 'download' },
  { key: 'add', label: t('retro.tabs.add'), icon: 'archive' },
])
const sysName = computed<Record<string, string>>(() => Object.fromEntries((lib.value?.systems ?? []).map((s: any) => [s.key, s.name])))
const streamed = (s: string) => lib.value?.systems?.find((x: any) => x.key === s)?.core === 'stream'
const enc = encodeURIComponent

// --- library ---
const q = ref('')
const sys = ref('')
const sort = ref<'az' | 'new'>('az')
const counts = computed(() => {
  const c: Record<string, number> = {}
  for (const g of lib.value?.games ?? []) c[g.sys] = (c[g.sys] ?? 0) + 1
  return c
})
const consoles = computed(() => (lib.value?.systems ?? []).filter((s: any) => counts.value[s.key]).sort((a: any, b: any) => a.gen - b.gen || a.name.localeCompare(b.name)))
const games = computed(() => {
  const words = q.value.toLowerCase().split(/\s+/).filter(Boolean)
  const list = (lib.value?.games ?? []).filter((g: any) => (!sys.value || g.sys === sys.value) && words.every(w => `${g.title} ${g.tags.join(' ')}`.toLowerCase().includes(w)))
  return sort.value === 'new' ? [...list].sort((a: any, b: any) => b.added - a.added) : list
})
const playUrl = (g: any) => `/api/retro/play?sys=${enc(g.sys)}&name=${enc(g.file)}`
const coverUrl = (g: any) => `/api/retro/file?sys=${enc(g.sys)}&kind=cover&name=${enc(g.cover)}`
const stream3ds = ref(false)
function del(g: any) {
  if (!arm(`${g.sys}/${g.file}`)) return
  run('retro_delete', { sys: g.sys, name: g.file }, refresh)
}
const startCt = () => run('ct_start', { vmid: lib.value?.ct }, refresh)

// --- free homebrew ---
const cat = ref<any[] | null>(null)
const catErr = ref('')
const cq = ref('')
const csys = ref('')
const shown = ref(60)
const getting = ref<Record<string, boolean>>({})
const info = ref<Record<string, string>>({})
watch(tab, (v) => { if (v === 'get' && !cat.value) loadCat() }, { immediate: true })
async function loadCat() {
  catErr.value = ''
  try { cat.value = (await $fetch<any>('/api/retro/catalog')).items } catch (e: any) { catErr.value = e?.data?.statusMessage || e?.message || 'failed' }
}
const catSys = computed(() => {
  const c: Record<string, number> = {}
  for (const i of cat.value ?? []) c[i.sys] = (c[i.sys] ?? 0) + 1
  return Object.entries(c).map(([key, n]) => ({ key, n, name: sysName.value[key] ?? key }))
})
const catList = computed(() => {
  const words = cq.value.toLowerCase().split(/\s+/).filter(Boolean)
  return (cat.value ?? []).filter(i => (!csys.value || i.sys === csys.value) && words.every(w => `${i.title} ${i.dev} ${i.tags.join(' ')}`.toLowerCase().includes(w)))
})
watch([cq, csys], () => (shown.value = 60))
async function grab(i: any) {
  getting.value[i.id] = true
  try {
    await $fetch('/api/retro/get', { method: 'POST', body: { id: i.id } })
    i.have = true
    toast(t('retro.added', { title: i.title }), { tone: 'ok' })
    refresh()
  } catch (e: any) { toast(e?.data?.statusMessage || e?.message || 'failed', { tone: 'bad' }) }
  finally { getting.value[i.id] = false }
}
async function more(i: any) {
  if (info.value[i.id] !== undefined) { delete info.value[i.id]; return }
  if (i.desc) { info.value[i.id] = i.desc; return }
  info.value[i.id] = '…'
  try { info.value[i.id] = (await $fetch<any>('/api/retro/info', { query: { id: i.id } })).text || t('retro.noInfo') } catch { info.value[i.id] = t('retro.noInfo') }
}
const playOf = (i: any) => `/api/retro/play?sys=${enc(i.sys)}&name=${enc(i.dest)}`

// --- own files ---
const usys = ref('')
const ukind = ref<'rom' | 'bios'>('rom')
const queue = ref<{ name: string, size: number, got: number, err?: string, done?: boolean }[]>([])
const busy = ref(false)
const uSystem = computed(() => lib.value?.systems?.find((s: any) => s.key === usys.value))
const accept = computed(() => ukind.value === 'bios' || !uSystem.value ? '' : [...uSystem.value.exts, ...(streamed(usys.value) ? [] : ['zip', '7z']), 'png', 'jpg'].map(e => `.${e}`).join(','))
const sharePath = computed(() => `\\\\${ip('games')}\\games\\roms\\<console>\\`)
const folders = computed(() => (lib.value?.systems ?? []).map((s: any) => `${s.key} = ${s.name}`).join(' · '))
const sortedSystems = computed(() => [...(lib.value?.systems ?? [])].sort((a: any, b: any) => a.gen - b.gen || a.name.localeCompare(b.name)))
const CHUNK = 6 * 2 ** 20
async function pick(ev: Event) {
  const files = [...((ev.target as HTMLInputElement).files ?? [])]
  ;(ev.target as HTMLInputElement).value = ''
  if (!files.length || !usys.value) return
  busy.value = true
  for (const f of files) {
    const row = reactive({ name: f.name, size: f.size, got: 0 } as any)
    queue.value.unshift(row)
    try {
      for (let off = 0; off < f.size; off += CHUNK) {
        const r: any = await $fetch('/api/retro/upload', {
          method: 'POST', body: f.slice(off, off + CHUNK), headers: { 'Content-Type': 'application/octet-stream' },
          query: { sys: usys.value, name: f.name, kind: ukind.value, offset: off, total: f.size },
        })
        row.got = r.got
      }
      row.done = true
    } catch (e: any) { row.err = e?.data?.statusMessage || e?.message || 'failed' }
  }
  busy.value = false
  refresh()
}
</script>

<template>
  <div>
    <PageTabs v-model="tab" :tabs="tabs" />
    <div v-if="error && !lib" class="errbox">{{ error.statusMessage || error.message }}</div>
    <Skeleton v-else-if="!lib" kind="tiles" />

    <!-- library -->
    <template v-else-if="tab === 'library'">
      <div class="bar">
        <input v-model="q" type="search" :placeholder="$t('retro.search')">
        <div class="seg">
          <button :class="{ on: sort === 'az' }" @click="sort = 'az'">A–Z</button>
          <button :class="{ on: sort === 'new' }" @click="sort = 'new'">{{ $t('retro.recent') }}</button>
        </div>
      </div>
      <div class="chips scroll-x">
        <button class="chip" :class="{ on: !sys }" @click="sys = ''">{{ $t('retro.all') }} · {{ lib.games.length }}</button>
        <button v-for="s in consoles" :key="s.key" class="chip" :class="{ on: sys === s.key }" @click="sys = sys === s.key ? '' : s.key">{{ s.name }} · {{ counts[s.key] }}</button>
      </div>

      <div v-if="!lib.games.length" class="empty-state">
        {{ $t('retro.empty') }}
        <div class="row center"><button class="btn primary" @click="tab = 'get'">{{ $t('retro.tabs.get') }}</button><button class="btn" @click="tab = 'add'">{{ $t('retro.tabs.add') }}</button></div>
      </div>
      <div v-else-if="!games.length" class="empty-state">{{ $t('retro.noMatch') }}</div>
      <div v-else class="tiles">
        <div v-for="g in games" :key="g.sys + g.file" class="game">
          <component :is="streamed(g.sys) ? 'button' : 'a'" class="art" :href="streamed(g.sys) ? undefined : playUrl(g)" @click="streamed(g.sys) && (stream3ds = true)">
            <img v-if="g.cover" :src="coverUrl(g)" alt="" loading="lazy">
            <span v-else class="ph">{{ sysName[g.sys] }}</span>
            <span class="play"><Icon :name="streamed(g.sys) ? 'ext' : 'play'" /></span>
          </component>
          <div class="meta">
            <div class="ttl" :title="g.file">{{ g.title }}</div>
            <div class="small muted line">
              <span class="pill">{{ sysName[g.sys] }}</span>
              <span v-if="g.saved" class="pill ok">{{ $t('retro.saved') }}</span>
              <span class="faint">{{ bytes(g.size) }}</span>
              <button class="lnk del" :class="{ sure: armed === g.sys + '/' + g.file }" @click="del(g)">{{ armed === g.sys + '/' + g.file ? $t('retro.sure') : 'Delete' }}</button>
            </div>
          </div>
        </div>
      </div>

      <Panel v-if="stream3ds" :title="$t('retro.stream.title')">
        <div v-if="lib.ctStatus !== 'running'" class="row">
          <span class="pill warn">{{ $t('retro.stream.off', { ct: lib.ct }) }}</span>
          <button class="btn sm primary" @click="startCt">{{ $t('retro.stream.start') }}</button>
        </div>
        <ol class="small steps">
          <li>{{ $t('retro.stream.s1') }}</li>
          <li>{{ $t('retro.stream.s2', { host: ip('games') }) }}</li>
          <li>{{ $t('retro.stream.s3') }}</li>
        </ol>
        <button class="btn sm ghost" @click="stream3ds = false">{{ $t('retro.close') }}</button>
      </Panel>
      <p class="small faint">{{ $t('retro.free', { n: bytes(lib.free) }) }}</p>
    </template>

    <!-- free homebrew -->
    <template v-else-if="tab === 'get'">
      <p class="small muted">{{ $t('retro.get.lead') }}</p>
      <div v-if="catErr" class="errbox">{{ catErr }} <button class="lnk" @click="loadCat">{{ $t('retro.retry') }}</button></div>
      <Skeleton v-else-if="!cat" kind="cards" />
      <template v-else>
        <div class="bar"><input v-model="cq" type="search" :placeholder="$t('retro.get.search', { n: cat.length })"></div>
        <div class="chips scroll-x">
          <button class="chip" :class="{ on: !csys }" @click="csys = ''">{{ $t('retro.all') }}</button>
          <button v-for="s in catSys" :key="s.key" class="chip" :class="{ on: csys === s.key }" @click="csys = csys === s.key ? '' : s.key">{{ s.name }} · {{ s.n }}</button>
        </div>
        <div v-if="!catList.length" class="empty-state">{{ $t('retro.noMatch') }}</div>
        <div class="cat">
          <div v-for="i in catList.slice(0, shown)" :key="i.id" class="item">
            <img v-if="i.cover" :src="i.cover" alt="" loading="lazy" class="thumb">
            <div v-else class="thumb ph">{{ sysName[i.sys] }}</div>
            <div class="body">
              <div class="ttl">{{ i.title }}</div>
              <div class="small muted line"><span class="pill">{{ sysName[i.sys] }}</span><span v-if="i.dev" class="clip">{{ i.dev }}</span></div>
              <div v-if="info[i.id]" class="small desc">{{ info[i.id] }}</div>
              <div class="row">
                <a v-if="i.have" class="btn sm primary" :href="playOf(i)"><Icon name="play" /> {{ $t('retro.play') }}</a>
                <button v-else class="btn sm primary" :disabled="getting[i.id]" @click="grab(i)"><Icon name="download" /> {{ getting[i.id] ? $t('retro.adding') : $t('retro.add') }}</button>
                <button class="btn sm ghost" @click="more(i)">{{ $t('retro.info') }}</button>
                <a class="lnk small" :href="i.link" target="_blank" rel="noopener">{{ i.src }}</a>
              </div>
            </div>
          </div>
        </div>
        <button v-if="catList.length > shown" class="btn ghost wide" @click="shown += 60">{{ $t('retro.more', { n: catList.length - shown }) }}</button>
      </template>
    </template>

    <!-- own files -->
    <template v-else>
      <Panel :title="$t('retro.up.title')">
        <div class="row">
          <select v-model="usys">
            <option value="" disabled>{{ $t('retro.up.console') }}</option>
            <option v-for="s in sortedSystems" :key="s.key" :value="s.key">{{ s.name }}</option>
          </select>
          <div class="seg">
            <button :class="{ on: ukind === 'rom' }" @click="ukind = 'rom'">{{ $t('retro.up.game') }}</button>
            <button :class="{ on: ukind === 'bios' }" :disabled="usys && streamed(usys)" @click="ukind = 'bios'">{{ $t('retro.up.biosBtn') }}</button>
          </div>
        </div>
        <p v-if="uSystem" class="small muted">
          {{ ukind === 'bios' ? $t('retro.up.bios', { has: lib.bios.includes(usys) ? $t('retro.up.biosHas') : '' }) : $t('retro.up.types', { exts: accept.replaceAll(',', ' ') }) }}
        </p>
        <label class="btn primary" :class="{ off: !usys || busy }">
          <Icon name="archive" /> {{ busy ? $t('retro.up.busy') : $t('retro.up.pick') }}
          <input type="file" multiple hidden :accept="accept" :disabled="!usys || busy" @change="pick">
        </label>
        <div v-for="(r, n) in queue" :key="n" class="small upl">
          <span class="clip">{{ r.name }}</span>
          <span v-if="r.err" class="bad">{{ r.err }}</span>
          <span v-else-if="r.done" class="pill ok">{{ $t('retro.up.done') }}</span>
          <span v-else class="num muted">{{ Math.floor(100 * r.got / r.size) }}%</span>
        </div>
      </Panel>
      <Panel :title="$t('retro.share.title')">
        <p class="small muted">{{ $t('retro.share.body') }}</p>
        <code class="mono small">{{ sharePath }}</code>
        <p class="small faint">{{ folders }}</p>
      </Panel>
      <p class="small faint">{{ $t('retro.legal') }}</p>
    </template>
  </div>
</template>

<style scoped>
.bar { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.bar input { flex: 1; min-width: 0; }
.chips { display: flex; gap: 6px; padding-bottom: 10px; }
.row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin: 6px 0; }
.row.center { justify-content: center; margin-top: 12px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; margin-bottom: 14px; }
.game { background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); overflow: hidden; display: flex; flex-direction: column; }
.art { position: relative; display: block; aspect-ratio: 4 / 3; background: var(--panel-2); border: 0; padding: 0; cursor: pointer; width: 100%; color: var(--muted); }
.art img { width: 100%; height: 100%; object-fit: cover; image-rendering: pixelated; }
.ph { position: absolute; inset: 0; display: grid; place-items: center; font-weight: 600; font-size: 13px; padding: 8px; text-align: center; }
.play { position: absolute; right: 8px; bottom: 8px; width: 34px; height: 34px; border-radius: 999px; display: grid; place-items: center; background: var(--accent); color: var(--bg); }
.meta { padding: 8px 10px 10px; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.ttl { font-weight: 600; font-size: 13.5px; line-height: 1.25; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.line { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.del { margin-left: auto; min-width: 28px; min-height: 28px; }
.cat { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 10px; margin-bottom: 12px; }
.item { display: flex; gap: 10px; background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); padding: 10px; min-width: 0; }
.thumb { width: 96px; height: 86px; flex-shrink: 0; object-fit: cover; border-radius: var(--radius-sm); background: var(--panel-2); image-rendering: pixelated; position: relative; font-size: 11px; color: var(--muted); }
.body { min-width: 0; flex: 1; display: flex; flex-direction: column; gap: 4px; }
.clip { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; }
.desc { white-space: pre-wrap; color: var(--muted); max-height: 180px; overflow: auto; }
.steps { padding-left: 18px; line-height: 1.6; }
.upl { display: flex; gap: 8px; justify-content: space-between; align-items: center; padding: 4px 0; border-top: 1px solid var(--line); }
.off { opacity: .5; pointer-events: none; }
.wide { width: 100%; }
@media (max-width: 640px) {
  .tiles { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .cat { grid-template-columns: 1fr; }
}
</style>
