<script setup lang="ts">
useHead({ title: 'Mail · Bastion' })

const tab = usePageTab('inbox')
const tabs = [{ key: 'inbox', label: 'Inbox' }, { key: 'accounts', label: 'Accounts' }, { key: 'categories', label: 'Categories' }]

const cats = ref<any[]>([])
const total = reactive({ count: 0, unread: 0 })
const enabledCats = computed(() => cats.value.filter(c => c.enabled))
const catOf = (id: string) => cats.value.find(c => c.id === id)
const ruleDone = ref('')
const accounts = ref<any[]>([])
const messages = ref<any[]>([])
const account = ref('')
const category = ref('')
const unread = ref(false)
const search = ref('')
const error = ref('')
const note = ref('')
const busy = ref('')
const cur = ref<any>(null)
const options = ref<any[]>([])
const form = reactive({ to: '', subject: '', text: '' })
const confirming = ref(false)
const sentOk = ref(false)

const msg = (e: any) => e?.data?.statusMessage || e?.message || 'failed'

async function load() {
  try {
    accounts.value = (await $fetch<any>('/api/mail/accounts')).accounts
    const c = await $fetch<any>('/api/mail/categories', { query: { account: account.value } })
    cats.value = c.categories; total.count = c.total; total.unread = c.total_unread
    messages.value = (await $fetch<any>('/api/mail/messages', { query: { account: account.value, category: category.value, unread: unread.value ? 1 : '', q: search.value } })).messages
    error.value = ''
  } catch (e: any) { error.value = msg(e) }
}
await load()
watch([account, category, unread], load)
let t: any
watch(search, () => { clearTimeout(t); t = setTimeout(load, 300) })

async function sync() {
  busy.value = 'sync'; note.value = ''
  try {
    const r = await $fetch<any>('/api/mail/sync', { method: 'POST', body: { account: account.value } })
    note.value = r.results.map((x: any) => x.error ? `${x.account}: ${x.error}` : `${x.account}: ${x.new} new${x.note ? ', ' + x.note : ''}`).join(' · ') || 'No account is set up yet'
    await load()
    const left = r.results.reduce((n: number, x: any) => n + (x.pending || 0), 0)
    if (left) {
      busy.value = 'sort'
      const out = await drainTriage(account.value, 6, (l: number) => { note.value = `Sorting… ${l} left` })
      note.value = out.left ? `${out.left} still to sort${out.note ? ': ' + out.note : ''}` : ''
      await load()
    }
  } catch (e: any) { error.value = msg(e) } finally { busy.value = '' }
}

async function open(m: any) {
  busy.value = 'open'; ruleDone.value = ''; options.value = []; confirming.value = false; sentOk.value = false
  try {
    cur.value = await $fetch<any>('/api/mail/message', { query: { account: m.account, uid: m.uid } })
    m.seen = 1
    const reply = cur.value.reply_to || cur.value.from || ''
    form.to = (reply.match(/<([^>]+)>/)?.[1] ?? reply).trim()
    form.subject = /^re:/i.test(cur.value.subject) ? cur.value.subject : `Re: ${cur.value.subject}`
    form.text = ''
    error.value = ''
  } catch (e: any) { error.value = msg(e) } finally { busy.value = '' }
}

async function setCat(id: string) {
  if (!cur.value || cur.value.category === id) return
  const was = cur.value.category
  try {
    await $fetch('/api/mail/message-category', { method: 'POST', body: { account: cur.value.account, uid: cur.value.uid, category: id, confirm: true } })
    cur.value.category = id; cur.value.source = 'manual'; ruleDone.value = ''
    const row = messages.value.find(x => x.account === cur.value.account && x.uid === cur.value.uid)
    if (row) { row.category = id; row.source = 'manual' }
    error.value = ''
  } catch (e: any) { cur.value.category = was; error.value = msg(e) }
}
const domainOf = (f: string) => (f.match(/@([^>\s]+)/)?.[1] ?? '').toLowerCase()
async function alwaysHere() {
  const d = domainOf(cur.value.from || '')
  try {
    await $fetch('/api/mail/categories-rule', { method: 'POST', body: { category: cur.value.category, kind: 'domain', value: d, apply: true, confirm: true } })
    ruleDone.value = `Mail from ${d} will go to ${catOf(cur.value.category)?.name ?? cur.value.category}.`
    error.value = ''
  } catch (e: any) { error.value = msg(e) }
}

async function draft() {
  busy.value = 'draft'
  try { options.value = (await $fetch<any>('/api/mail/drafts', { method: 'POST', body: { account: cur.value.account, uid: cur.value.uid } })).options; error.value = '' }
  catch (e: any) { error.value = msg(e) } finally { busy.value = '' }
}

async function send() {
  if (!confirming.value) { confirming.value = true; return }
  busy.value = 'send'
  try {
    await $fetch('/api/mail/send', { method: 'POST', body: { account: cur.value.account, to: form.to, subject: form.subject, text: form.text, in_reply_to: cur.value.message_id, references: cur.value.references, confirm: true } })
    sentOk.value = true; confirming.value = false; error.value = ''
  } catch (e: any) { error.value = msg(e); confirming.value = false } finally { busy.value = '' }
}

const when = (s: number) => {
  const d = new Date(s * 1000)
  return Date.now() - d.getTime() < 86_400_000 ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : d.toLocaleDateString([], { day: 'numeric', month: 'short' })
}
const who = (f: string) => (f.match(/^\s*"?([^"<]+?)"?\s*</)?.[1] ?? f).trim()
const label = (id: string) => accounts.value.find(a => a.id === id)?.label ?? id
</script>

<template>
  <div class="mail">
    <PageTabs v-if="!cur" v-model="tab" :tabs="tabs" />
    <MailAccounts v-if="tab === 'accounts' && !cur" @changed="load" />
    <MailCategories v-else-if="tab === 'categories' && !cur" @changed="load" />
    <template v-else>
    <p v-if="error" class="errbox">{{ error }}</p>
    <p v-if="note" class="faint small">{{ note }}</p>

    <div v-if="!cur && !accounts.length" class="empty-state">
      <p>No mail account yet.</p>
      <button type="button" class="btn primary" @click="navigateTo({ query: { s: 'accounts', add: '1' } })">Add account</button>
    </div>
    <template v-else-if="!cur">
      <div class="row">
        <button type="button" class="btn" :class="{ primary: !account }" @click="account = ''">All</button>
        <button v-for="a in accounts" :key="a.id" type="button" class="btn" :class="{ primary: account === a.id }" @click="account = a.id">{{ a.label }}</button>
        <span class="sp" />
        <button type="button" class="btn" :disabled="busy === 'sync' || busy === 'sort'" @click="sync">{{ busy === 'sync' ? 'Syncing…' : busy === 'sort' ? 'Sorting…' : 'Sync' }}</button>
      </div>
      <div class="row">
        <button type="button" class="chip" :class="{ on: !category }" @click="category = ''">All<span v-if="total.unread" class="faint"> {{ total.unread }}</span></button>
        <button v-for="c in enabledCats" :key="c.id" type="button" class="chip" :class="{ on: category === c.id }" @click="category = c.id">{{ c.name }}<span v-if="c.unread" class="faint"> {{ c.unread }}</span></button>
        <button type="button" class="chip" :class="{ on: unread }" @click="unread = !unread">Unread</button>
      </div>
      <input v-model="search" class="find" type="search" placeholder="Search sender, subject, summary">

      <p v-if="!messages.length" class="faint">No mail cached. Tap Sync.</p>
      <ul class="list">
        <li v-for="m in messages" :key="m.account + m.uid" :class="{ unread: !m.seen }" @click="open(m)">
          <div class="top"><b class="from">{{ who(m.from) }}</b><span class="faint small">{{ when(m.date) }}</span></div>
          <div class="subj">{{ m.subject }}</div>
          <div class="muted small">{{ m.summary || m.snippet }}</div>
          <div class="pills"><MailCatPill v-if="m.category && catOf(m.category)" :name="catOf(m.category).name" :color="catOf(m.category).color" /><span v-if="!account && accounts.length > 1" class="pill">{{ label(m.account) }}</span></div>
        </li>
      </ul>
    </template>

    <template v-else>
      <button type="button" class="btn" @click="cur = null"><Icon name="chevron-left" :size="16" /> Back</button>
      <h2 class="subj">{{ cur.subject }}</h2>
      <div class="muted small">{{ cur.from }} · {{ when(cur.date) }}</div>
      <div class="row">
        <button v-for="c in enabledCats" :key="c.id" type="button" class="chip" :class="{ on: cur.category === c.id }" @click="setCat(c.id)">{{ c.name }}</button>
      </div>
      <div v-if="cur.source === 'manual' && domainOf(cur.from || '')" class="row">
        <button v-if="!ruleDone" type="button" class="btn sm" @click="alwaysHere">Always sort mail from {{ domainOf(cur.from) }} here</button>
        <span v-else class="small muted">{{ ruleDone }}</span>
      </div>
      <pre class="text">{{ cur.text || '(empty)' }}</pre>

      <button type="button" class="btn primary" :disabled="busy === 'draft'" @click="draft">{{ busy === 'draft' ? 'Writing drafts…' : 'Draft replies' }}</button>
      <div class="cards">
        <button v-for="(o, i) in options" :key="i" type="button" class="card" @click="form.text = o.text">
          <b>{{ o.label }}</b><span class="muted small">{{ o.text }}</span>
        </button>
      </div>

      <form class="reply" @submit.prevent="send">
        <input v-model="form.to" type="email" placeholder="To">
        <input v-model="form.subject" placeholder="Subject">
        <textarea v-model="form.text" rows="8" placeholder="Your reply" @input="confirming = false" />
        <p v-if="sentOk" class="ok">Sent.</p>
        <div class="row">
          <button type="submit" class="btn" :class="{ primary: confirming }" :disabled="!form.text.trim() || !form.to || busy === 'send'">
            {{ confirming ? `Tap again to send to ${form.to}` : 'Send' }}
          </button>
          <button v-if="confirming" type="button" class="btn" @click="confirming = false">Cancel</button>
        </div>
      </form>
    </template>
    </template>
  </div>
</template>

<style scoped>
.mail { display: flex; flex-direction: column; gap: 10px; max-width: 760px; }
.row, .pills { display: flex; flex-wrap: wrap; gap: 8px 10px; align-items: center; }
@media (pointer: coarse) { .row .btn { min-height: 38px; } .row .chip { min-height: 36px; } }
.sp { flex: 1; }
.find, .reply input, .reply textarea { width: 100%; box-sizing: border-box; font: inherit; }
.list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.list li { padding: 10px; border-radius: 10px; background: var(--card, rgba(127,127,127,.1)); cursor: pointer; display: flex; flex-direction: column; gap: 3px; }
.list li.unread .from, .list li.unread .subj { font-weight: 700; }
.top { display: flex; justify-content: space-between; gap: 8px; }
.from, .subj { overflow-wrap: anywhere; }
.text { white-space: pre-wrap; overflow-wrap: anywhere; font: inherit; background: var(--card, rgba(127,127,127,.1)); padding: 10px; border-radius: 10px; margin: 0; }
.cards { display: flex; flex-direction: column; gap: 6px; }
.card { text-align: left; padding: 10px; border-radius: 10px; border: 1px solid rgba(127,127,127,.3); background: none; color: inherit; font: inherit; display: flex; flex-direction: column; gap: 3px; }
.reply { display: flex; flex-direction: column; gap: 8px; }
</style>
