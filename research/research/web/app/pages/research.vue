<script setup lang="ts">
useHead({ title: 'Research · Bastion' })

const DEPTHS = [
  { id: 'quick', label: 'Quick', note: '~5 min' },
  { id: 'thorough', label: 'Thorough', note: '~20 min' },
  { id: 'overnight', label: 'Overnight', note: 'hours' },
]
const runs = ref<any[]>([])
const loaded = ref(false)
const error = ref('')
const question = ref('')
const depth = ref('thorough')
const busy = ref(false)

async function load() {
  try {
    runs.value = (await $fetch<{ runs: any[] }>('/api/research')).runs
    error.value = ''
  } catch (e: any) { error.value = e?.statusMessage || e?.message } finally { loaded.value = true }
}
// fast while something is being worked on, otherwise only on the tab coming back
usePoll(() => load(), 4000)

async function post(body: Record<string, any>) {
  try {
    const r = await $fetch<any>('/api/research/action', { method: 'POST', body })
    error.value = ''
    await load()
    return r
  } catch (e: any) { error.value = e?.data?.statusMessage || e?.statusMessage || e?.message }
}
async function ask() {
  if (!question.value.trim() || busy.value) return
  busy.value = true
  const r = await post({ action: 'ask', question: question.value, depth: depth.value })
  if (r) question.value = ''
  busy.value = false
}

// the open report lives in the URL, so the phone's back button closes it
const route = useRoute(), router = useRouter()
const openId = computed(() => Number(route.query.r) || null)
const open = ref<any>(null)
watch(openId, async (id) => {
  open.value = null
  if (!id) return
  try { open.value = await $fetch<any>('/api/research', { query: { id } }) } catch { router.replace({ query: { ...route.query, r: undefined } }) }
}, { immediate: true })
const show = (id: number) => router.push({ query: { ...route.query, r: id } })
function close() { if (window.history.state?.back) router.back(); else router.replace({ query: { ...route.query, r: undefined } }) }
const html = computed(() => (open.value?.report ? noteHtml(open.value.report) : ''))

const { armed, arm } = useArm()
async function remove(id: number) {
  if (!arm(`del${id}`)) return
  await post({ action: 'delete', id })
  if (openId.value === id) close()
}
const { toast } = useToast()
async function toNotes(id: number) {
  if (await post({ action: 'note', id })) toast("Saved to Notes", { tone: "ok" })
}
const active = (r: any) => r.status === 'queued' || r.status === 'running'
const when = (t: number) => new Date(t * 1000).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
</script>

<template>
  <div>
    <template v-if="openId">
      <button class="lnk" @click="close"><Icon name="chevron-left" :size="14"/> Back</button>
      <Skeleton v-if="!open" kind="lines" />
      <Panel v-else :title="open.question">
        <div class="row" style="gap:8px;flex-wrap:wrap;margin-bottom:10px">
          <span class="pill" :class="open.status === 'done' ? 'ok' : open.status === 'failed' ? 'bad' : ''">{{ open.status }}</span>
          <span class="muted small">{{ open.depth }} · {{ open.sources.length }} sources · {{ when(open.created) }}</span>
        </div>
        <div v-if="open.report" class="md body" v-html="html" />
        <div v-else-if="open.error" class="errbox">{{ open.error }}</div>
        <p v-else class="muted small">{{ open.step || 'Waiting…' }}</p>
        <div class="row" style="gap:8px;flex-wrap:wrap;margin-top:12px">
          <button v-if="open.report" class="btn sm" @click="toNotes(open.id)">Save to Notes</button>
          <button class="btn sm danger" :class="{ sure: armed === `del${open.id}` }" @click="remove(open.id)">{{ armed === `del${open.id}` ? 'Sure?' : 'Delete' }}</button>
        </div>
      </Panel>
    </template>

    <template v-else>
      <h2 class="sec">Research</h2>
      <div v-if="error" class="errbox">{{ error }}</div>
      <Panel title="Ask">
        <textarea v-model="question" rows="3" maxlength="500" placeholder="What do you want to find out?" style="width:100%" />
        <div class="row" style="gap:8px;flex-wrap:wrap;margin-top:8px;align-items:center">
          <div class="seg">
            <button v-for="d in DEPTHS" :key="d.id" :class="{ on: depth === d.id }" @click="depth = d.id">{{ d.label }}</button>
          </div>
          <span class="muted small">{{ DEPTHS.find(d => d.id === depth)?.note }}</span>
          <button class="btn primary" style="margin-left:auto" :disabled="!question.trim() || busy" @click="ask">Research</button>
        </div>
      </Panel>

      <Skeleton v-if="!loaded" kind="rows" />
      <p v-else-if="!runs.length" class="empty-state">Nothing yet.</p>
      <div v-else class="grid" style="margin-top:12px">
        <Panel v-for="r in runs" :key="r.id">
          <div class="row" style="gap:8px;align-items:flex-start">
            <button class="lnk" style="text-align:left;flex:1" @click="show(r.id)">{{ r.question }}</button>
            <span class="pill" :class="r.status === 'done' ? 'ok' : r.status === 'failed' ? 'bad' : r.status === 'running' ? 'accent' : ''">{{ r.status }}</span>
          </div>
          <p class="muted small" style="margin-top:4px">
            {{ r.depth }} · {{ when(r.created) }}<template v-if="r.nsources"> · {{ r.nsources }} sources</template>
            <template v-if="r.status === 'running'"> · {{ r.step }}</template>
          </p>
          <p v-if="r.error" class="small" style="color:var(--bad)">{{ r.error }}</p>
          <div class="row" style="gap:8px;margin-top:6px">
            <button v-if="active(r)" class="btn sm" @click="post({ action: 'cancel', id: r.id })">Cancel</button>
            <button v-if="r.status === 'done'" class="btn sm" @click="show(r.id)">Open</button>
            <button v-if="r.status !== 'running'" class="btn sm danger" :class="{ sure: armed === `del${r.id}` }" @click="remove(r.id)">{{ armed === `del${r.id}` ? 'Sure?' : 'Delete' }}</button>
          </div>
        </Panel>
      </div>
    </template>
  </div>
</template>
