<script setup lang="ts">
useHead({ title: 'Trending repos · Bastion' })

type Repo = { repo: string, descr: string, lang: string, stars: number, gain: number, sources: string[], summary: string, tags: string[], runs: string, score: number, state: string, starred: number }
type Msg = { role: 'user' | 'assistant', content: string }

const tab = usePageTab('new')
const data = ref<{ repos: Repo[], counts: Record<string, number>, status: any }>()
const error = ref('')
async function load() {
  try {
    data.value = await $fetch('/api/trending-repos', { query: { state: tab.value } })
    error.value = ''
  } catch (e: any) { error.value = e?.statusMessage || e?.message }
}
// fast while the list is being refreshed, otherwise only when the tab comes back
usePoll(() => load(), 5000)
watch(tab, () => { data.value = undefined; load() })

const tabs = computed(() => [
  { key: 'new', label: 'For you', badge: data.value?.counts.new || undefined },
  { key: 'saved', label: 'To try', badge: data.value?.counts.saved || undefined },
  { key: 'dismissed', label: 'Dismissed' },
])

async function post(body: Record<string, any>) {
  try {
    const r = await $fetch<any>('/api/trending-repos/action', { method: 'POST', body })
    error.value = ''
    return r
  } catch (e: any) { error.value = e?.data?.statusMessage || e?.statusMessage || e?.message; return null }
}

// moving a card is optimistic: it leaves the list at once and comes back if the save fails
async function move(r: Repo, action: 'save' | 'dismiss' | 'restore') {
  const before = data.value!.repos
  data.value!.repos = before.filter(x => x.repo !== r.repo)
  if (!(await post({ action, repo: r.repo }))) data.value!.repos = before
  else load()
}
const { toast } = useToast()
async function star(r: Repo) {
  const on = !r.starred
  r.starred = on ? 1 : 0
  if (!(await post({ action: on ? 'star' : 'unstar', repo: r.repo }))) r.starred = on ? 0 : 1
}
async function toNotes(r: Repo) {
  if (await post({ action: 'note', repo: r.repo })) toast('Saved to Notes', { tone: 'ok' })
}

// the open card holds a small chat about that repo; it lives in the page only
const openRepo = ref('')
const chats = reactive<Record<string, Msg[]>>({})
const draft = ref('')
const asking = ref(false)
function toggle(r: Repo) { openRepo.value = openRepo.value === r.repo ? '' : r.repo; draft.value = '' }
async function ask(r: Repo) {
  const q = draft.value.trim()
  if (!q || asking.value) return
  const h = (chats[r.repo] ??= [])
  h.push({ role: 'user', content: q })
  draft.value = ''
  asking.value = true
  const res = await post({ action: 'ask', repo: r.repo, history: h })
  h.push({ role: 'assistant', content: res?.answer || 'No answer. Try again.' })
  asking.value = false
}
const QUICK = ['How do I run it?', 'Would it fit my RTX 3060?', 'What does it replace?']

const interests = ref('')
const showInt = ref(false)
watch(() => data.value?.status.interests, (v) => { if (v && !showInt.value) interests.value = v }, { immediate: true })
async function saveInterests() {
  if (await post({ action: 'interests', text: interests.value })) { toast('Interests saved, used for the next refresh', { tone: 'ok' }); showInt.value = false }
}
async function refresh() {
  if (await post({ action: 'refresh' })) { toast('Refreshing', { tone: 'ok' }); load() }
}

const k = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k` : String(n))
const when = (t: number) => (t ? new Date(t * 1000).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'never')
const tone = (s: number) => (s >= 70 ? 'ok' : s >= 40 ? 'accent' : '')
</script>

<template>
  <div>
    <h2 class="sec">Trending repos</h2>
    <PageTabs v-model="tab" :tabs="tabs" />
    <div v-if="error" class="errbox">{{ error }}</div>

    <div class="row" style="gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0">
      <span class="muted small">
        <template v-if="data?.status.busy">{{ data.status.step || 'Working' }}</template>
        <template v-else>Updated {{ when(data?.status.last ?? 0) }}</template>
      </span>
      <button class="btn sm" style="margin-left:auto" @click="showInt = !showInt">Interests</button>
      <button class="btn sm" :disabled="data?.status.busy" @click="refresh"><Icon name="refresh-cw" :size="14" /> Refresh</button>
    </div>
    <p v-if="data?.status.error" class="small" style="color:var(--bad)">{{ data.status.error }}</p>

    <Panel v-if="showInt" title="Interests">
      <textarea v-model="interests" rows="3" maxlength="600" style="width:100%" />
      <div class="row" style="gap:8px;margin-top:8px"><button class="btn primary sm" @click="saveInterests">Save</button></div>
    </Panel>

    <Skeleton v-if="!data" kind="cards" />
    <p v-else-if="!data.repos.length" class="empty-state">{{ tab === 'new' ? 'Nothing new. Refresh or check back tomorrow.' : 'Nothing yet.' }}</p>
    <div v-else class="grid" style="margin-top:8px">
      <Panel v-for="r in data.repos" :key="r.repo">
        <div class="row" style="gap:8px;align-items:flex-start">
          <button class="lnk" style="text-align:left;flex:1;font-weight:600;word-break:break-word" @click="toggle(r)">{{ r.repo }}</button>
          <span v-if="r.score" class="pill" :class="tone(r.score)">{{ r.score }}%</span>
        </div>
        <div class="row" style="gap:6px;flex-wrap:wrap;margin:6px 0">
          <span v-if="r.lang" class="pill">{{ r.lang }}</span>
          <span class="pill"><Icon name="star" :size="12" /> {{ k(r.stars) }}</span>
          <span v-if="r.gain" class="pill accent">+{{ k(r.gain) }}</span>
          <span v-for="t in r.tags" :key="t" class="pill">{{ t }}</span>
        </div>
        <p class="small" style="margin:4px 0">{{ r.summary || r.descr }}</p>
        <p v-if="r.runs" class="muted small" style="margin:4px 0">{{ r.runs }}</p>

        <div class="row" style="gap:8px;flex-wrap:wrap;margin-top:8px">
          <button class="btn sm" :class="{ primary: openRepo === r.repo }" @click="toggle(r)">Ask</button>
          <button class="btn sm" @click="star(r)"><Icon name="star" :size="14" /> {{ r.starred ? 'Starred' : 'Star' }}</button>
          <button v-if="r.state === 'new'" class="btn sm" @click="move(r, 'save')"><Icon name="bookmark" :size="14" /> To try</button>
          <button v-if="r.state === 'new' || r.state === 'saved'" class="btn sm" @click="move(r, 'dismiss')"><Icon name="x" :size="14" /> Remove</button>
          <button v-if="r.state !== 'new'" class="btn sm" @click="move(r, 'restore')">Restore</button>
          <button class="btn sm" @click="toNotes(r)">Notes</button>
          <a class="btn sm" :href="`https://github.com/${r.repo}`" target="_blank" rel="noopener">GitHub</a>
        </div>

        <div v-if="openRepo === r.repo" style="margin-top:10px;border-top:1px solid var(--line);padding-top:10px">
          <div v-for="(m, i) in chats[r.repo] ?? []" :key="i" class="small" :class="m.role === 'user' ? 'muted' : ''" style="margin:6px 0;white-space:pre-wrap">
            <b v-if="m.role === 'user'">You: </b>{{ m.content }}
          </div>
          <p v-if="asking" class="muted small">Reading the README…</p>
          <div v-if="!(chats[r.repo] ?? []).length" class="row" style="gap:6px;flex-wrap:wrap;margin-bottom:6px">
            <button v-for="q in QUICK" :key="q" class="chip" @click="draft = q; ask(r)">{{ q }}</button>
          </div>
          <div class="row" style="gap:8px">
            <input v-model="draft" style="flex:1" maxlength="400" placeholder="Ask about this repo" @keydown.enter.prevent="ask(r)">
            <button class="btn primary sm" :disabled="!draft.trim() || asking" @click="ask(r)">Send</button>
          </div>
        </div>
      </Panel>
    </div>
  </div>
</template>

<style scoped>
.row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.row input { min-width: 0; }
</style>
