<script setup lang="ts">
/** Mail -> Accounts: list, add, edit, test and remove mail accounts. The agent stores the rows and the passwords; no password ever comes back. */
const emit = defineEmits<{ (e: 'changed'): void }>()
const open = ref(false)

// hosts of the presets; TU Berlin's are unverified (guessed from memory, not tried)
const PRESETS: Record<string, { name: string, imap_host: string, imap_port: number, smtp_host: string, smtp_port: number, hint?: string }> = {
  gmail: { name: 'Gmail', imap_host: 'imap.gmail.com', imap_port: 993, smtp_host: 'smtp.gmail.com', smtp_port: 587, hint: 'Use an app password (needs 2-step verification)' },
  workspace: { name: 'Google Workspace', imap_host: 'imap.gmail.com', imap_port: 993, smtp_host: 'smtp.gmail.com', smtp_port: 587, hint: 'Use an app password (needs 2-step verification)' },
  microsoft: { name: 'Microsoft 365 / Outlook', imap_host: 'outlook.office365.com', imap_port: 993, smtp_host: 'smtp.office365.com', smtp_port: 587, hint: 'Basic login may be blocked by your admin' },
  tuberlin: { name: 'TU Berlin', imap_host: 'imap.tu-berlin.de', imap_port: 993, smtp_host: 'smtp.tu-berlin.de', smtp_port: 587 },
  gmx: { name: 'GMX', imap_host: 'imap.gmx.net', imap_port: 993, smtp_host: 'mail.gmx.net', smtp_port: 587 },
  webde: { name: 'web.de', imap_host: 'imap.web.de', imap_port: 993, smtp_host: 'smtp.web.de', smtp_port: 587 },
  other: { name: 'Other', imap_host: '', imap_port: 993, smtp_host: '', smtp_port: 587 },
}

const accounts = ref<any[] | null>(null)
const error = ref('')
const { armed, arm } = useArm()
const testing = ref('')
const results = reactive<Record<string, { ok: boolean, text: string }>>({})

async function load() {
  try { accounts.value = (await $fetch<any>('/api/mail/accounts')).accounts; error.value = '' }
  catch (e: any) { error.value = errText(e) }
}
const errText = (e: any) => e?.data?.statusMessage || e?.data?.message || e?.message || 'failed'
await load()

const status = (a: any) => a.last_error ? { cls: 'bad', text: 'Error' } : !a.configured ? { cls: 'warn', text: 'Password missing' } : { cls: 'ok', text: 'Connected' }
const ago = (s: number | null) => {
  if (!s) return 'never'
  const m = Math.round((Date.now() / 1000 - s) / 60)
  return m < 1 ? 'just now' : m < 60 ? `${m} min ago` : m < 1440 ? `${Math.round(m / 60)} h ago` : `${Math.round(m / 1440)} d ago`
}

async function testSaved(a: any) {
  testing.value = a.id
  try {
    const r = await $fetch<any>('/api/mail/account-test', { method: 'POST', body: { id: a.id } })
    results[a.id] = { ok: r.ok, text: r.ok ? 'Login works (IMAP and SMTP)' : r.error }
  } catch (e: any) { results[a.id] = { ok: false, text: errText(e) } } finally { testing.value = '' }
}

async function remove(a: any) {
  if (!arm('rm' + a.id)) return
  try { await $fetch('/api/mail/account-delete', { method: 'POST', body: { id: a.id, delete_cache: true, confirm: true } }); await load(); emit('changed') }
  catch (e: any) { error.value = errText(e) }
}

// ---- form ----
const blank = () => ({ id: '', provider: '', label: '', email: '', username: '', password: '', imap_host: '', imap_port: 993, smtp_host: '', smtp_port: 587 })
const f = reactive(blank())
const hadPw = ref(false)
const userTouched = ref(false)
const showServer = ref(false)
const showPw = ref(false)
const busy = ref('')
const formErr = ref('')
const failed = ref(false)
const preset = computed(() => PRESETS[f.provider])
const isOther = computed(() => f.provider === 'other')

function startAdd() { Object.assign(f, blank()); hadPw.value = false; userTouched.value = false; showServer.value = false; formErr.value = ''; failed.value = false; open.value = true }
function startEdit(a: any) {
  Object.assign(f, blank(), { id: a.id, provider: a.provider || 'other', label: a.label, email: a.from, username: a.username, imap_host: a.imap_host, imap_port: a.imap_port, smtp_host: a.smtp_host, smtp_port: a.smtp_port })
  hadPw.value = a.configured; userTouched.value = a.username !== a.from; showServer.value = false; formErr.value = ''; failed.value = false; open.value = true
}
function pick(k: string) {
  f.provider = k
  const p = PRESETS[k]
  if (k !== 'other') Object.assign(f, { imap_host: p.imap_host, imap_port: p.imap_port, smtp_host: p.smtp_host, smtp_port: p.smtp_port })
  if (!f.label && k !== 'other') f.label = p.name
  showServer.value = k === 'other'
}
watch(() => f.email, (v) => { if (!userTouched.value) f.username = v })

const payload = () => ({ ...f, username: f.username || f.email })
const canSave = computed(() => f.provider && f.label.trim() && f.email.trim() && (hadPw.value || f.password) && f.imap_host && f.smtp_host)

async function submit(force = false) {
  busy.value = force ? 'save' : 'test'; formErr.value = ''
  try {
    if (!force) {
      const r = await $fetch<any>('/api/mail/account-test', { method: 'POST', body: payload() })
      if (!r.ok) { formErr.value = r.error; failed.value = true; return }
    }
    busy.value = 'save'
    await $fetch('/api/mail/account-save', { method: 'POST', body: { ...payload(), confirm: true } })
    open.value = false
    await load(); emit('changed')
  } catch (e: any) { formErr.value = errText(e); failed.value = false } finally { busy.value = '' }
}
if (useRoute().query.add) startAdd() // arrives from the inbox's empty state
</script>

<template>
  <div class="accts">
    <p v-if="error" class="errbox">{{ error }}</p>

    <Panel v-if="open" id="mail-acct-form" :title="f.id ? 'Edit account' : 'Add account'" fold="open">
      <form class="form" autocomplete="off" @submit.prevent="submit(false)">
        <div class="chips">
          <button v-for="(p, k) in PRESETS" :key="k" type="button" class="chip" :class="{ on: f.provider === k }" @click="pick(String(k))">{{ p.name }}</button>
        </div>
        <template v-if="f.provider">
          <label>Name<input v-model="f.label" maxlength="40" placeholder="Uni" autocomplete="off"></label>
          <label>Email address<input v-model="f.email" type="email" inputmode="email" autocapitalize="off" autocomplete="off" placeholder="you@example.org"></label>
          <label>Username<input v-model="f.username" autocapitalize="off" autocomplete="off" @input="userTouched = true"></label>
          <label>Password
            <span class="pw-row">
              <input v-model="f.password" :type="showPw ? 'text' : 'password'" autocomplete="off" autocapitalize="off" spellcheck="false" :placeholder="hadPw ? 'Saved' : ''">
              <button type="button" class="btn ghost sm" @click="showPw = !showPw">{{ showPw ? 'Hide' : 'Show' }}</button>
            </span>
            <span v-if="preset?.hint" class="faint small">{{ preset.hint }}</span>
          </label>
          <button v-if="!isOther" type="button" class="lnk small" @click="showServer = !showServer">{{ showServer ? 'Hide server settings' : 'Server settings' }}</button>
          <div v-if="showServer || isOther" class="srv">
            <label>IMAP host<input v-model="f.imap_host" autocapitalize="off" autocomplete="off"></label>
            <label>IMAP port<input v-model="f.imap_port" inputmode="numeric" autocomplete="off"></label>
            <label>SMTP host<input v-model="f.smtp_host" autocapitalize="off" autocomplete="off"></label>
            <label>SMTP port<input v-model="f.smtp_port" inputmode="numeric" autocomplete="off"></label>
          </div>
          <p v-if="formErr" class="errbox">{{ formErr }}</p>
          <div class="row">
            <button type="submit" class="btn primary" :disabled="!canSave || !!busy">{{ busy === 'test' ? 'Testing…' : busy === 'save' ? 'Saving…' : 'Test and save' }}</button>
            <button v-if="failed" type="button" class="btn" :disabled="!!busy" @click="submit(true)">Save anyway</button>
            <button type="button" class="btn ghost" :disabled="!!busy" @click="open = false">Cancel</button>
          </div>
        </template>
      </form>
    </Panel>

    <Skeleton v-if="accounts === null" kind="cards" />
    <template v-else>
      <div v-if="!open" class="row"><button type="button" class="btn primary" @click="startAdd"><Icon name="plus" :size="16" /> Add account</button></div>
      <p v-if="!accounts.length && !open" class="empty-state">No accounts yet.</p>
      <Panel v-for="a in accounts" :key="a.id" :id="'mail-acct-' + a.id" :title="a.label" :sub="a.from" fold="open">
        <div class="meta">
          <span class="pill" :class="status(a).cls">{{ status(a).text }}</span>
          <span class="faint small">{{ PRESETS[a.provider]?.name || 'Other' }}</span>
          <span class="faint small">Synced {{ ago(a.last_sync) }}</span>
          <span class="faint small">{{ a.unread }} unread of {{ a.messages }}</span>
        </div>
        <p v-if="a.last_error" class="errbox">{{ a.last_error }}</p>
        <p v-if="results[a.id]" :class="results[a.id].ok ? 'small' : 'errbox'">{{ results[a.id].text }}</p>
        <div class="row">
          <button type="button" class="btn sm" :disabled="testing === a.id" @click="testSaved(a)">{{ testing === a.id ? 'Testing…' : 'Test' }}</button>
          <button type="button" class="btn sm" @click="startEdit(a)">Edit</button>
          <button type="button" class="btn sm danger" :class="{ sure: armed === 'rm' + a.id }" @click="remove(a)">{{ armed === 'rm' + a.id ? 'Sure?' : 'Remove' }}</button>
        </div>
      </Panel>
    </template>
  </div>
</template>

<style scoped>
.accts { display: flex; flex-direction: column; gap: 10px; }
.chips, .row, .meta { display: flex; flex-wrap: wrap; gap: 8px 10px; align-items: center; }
.row { margin-top: 12px; }
.meta { margin-bottom: 6px; }
.errbox { margin: 8px 0 0; }
@media (pointer: coarse) { .row .btn { min-height: 38px; padding-inline: 14px; } }
.form { display: flex; flex-direction: column; gap: 10px; }
.form label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: var(--muted); }
.form input { width: 100%; box-sizing: border-box; font: inherit; min-height: 36px; }
.pw-row { display: flex; gap: 8px; align-items: center; }
.pw-row input { flex: 1; min-width: 0; }
.srv { display: grid; grid-template-columns: 1fr 90px; gap: 10px; }
@media (max-width: 640px) { .srv { grid-template-columns: 1fr 80px; } }
@media (pointer: coarse) { .btn.sm, .chip, .lnk { min-height: 36px; } }
</style>
