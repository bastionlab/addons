<script setup lang="ts">
const { t } = useI18n()
useHead({ title: 'Aliases · pve' })

interface Alias { address: string, label: string, note: string, active: boolean | null, created: number, checked: number }
interface List { user: string | null, signed_in: boolean, pending: string | null, aliases: Alias[] }

const { data, error, refresh } = useFetch<List>('/api/aliases', { server: false })
const { toast, optimistic } = useToast()
const { armed, arm } = useArm()

const busy = ref('')
const err = (e: any) => e?.data?.statusMessage || e?.statusMessage || e?.message || 'failed'
async function call<T = any>(action: string, body: Record<string, any> = {}) {
  return $fetch<T>('/api/aliases/action', { method: 'POST', body: { action, ...body } })
}
async function step(key: string, fn: () => Promise<any>) {
  busy.value = key
  try { await fn() } catch (e) { toast(err(e), { tone: 'bad' }) } finally { busy.value = '' }
}

// sign in: username → code from the mail
const user = ref('')
const otp = ref('')
const login = () => step('login', async () => { await call('login', { user: user.value }); await refresh() })
const verify = () => step('verify', async () => { data.value = await call<List>('verify', { otp: otp.value }); otp.value = '' })
const logout = () => step('logout', async () => { data.value = await call<List>('logout') })

// new alias: copied at once, that's what you need it for
const label = ref('')
const fresh = ref('')
async function copy(a: string) {
  try { await navigator.clipboard.writeText(a); toast(t('aliases.copied', { a })) } catch { toast(a) }
}
const make = () => step('new', async () => {
  const a = await call<Alias>('new', { label: label.value })
  data.value?.aliases.unshift(a)
  fresh.value = a.address
  label.value = ''
  await copy(a.address)
})

const q = ref('')
const show = ref<'all' | 'on' | 'off'>('all')
const list = computed(() => {
  const s = q.value.trim().toLowerCase()
  return (data.value?.aliases ?? []).filter(a =>
    (show.value === 'all' || (show.value === 'on' ? a.active !== false : a.active === false))
    && (!s || `${a.address} ${a.label} ${a.note}`.toLowerCase().includes(s)))
})
const counts = computed(() => {
  const all = data.value?.aliases ?? []
  return { all: all.length, on: all.filter(a => a.active !== false).length, off: all.filter(a => a.active === false).length }
})

function toggle(a: Alias) {
  const was = a.active
  optimistic(() => (a.active = !(was !== false)), () => (a.active = was),
    () => call('active', { address: a.address, active: a.active }), t('aliases.change'))
}

const editing = ref('')
const draft = reactive({ label: '', note: '' })
function edit(a: Alias) { editing.value = a.address; draft.label = a.label; draft.note = a.note }
const save = (a: Alias) => step(`e:${a.address}`, async () => {
  Object.assign(a, await call<Alias>('edit', { address: a.address, ...draft }))
  editing.value = ''
})
function remove(a: Alias) {
  if (!arm(`d:${a.address}`)) return
  step(`d:${a.address}`, async () => {
    await call('delete', { address: a.address })
    if (data.value) data.value.aliases = data.value.aliases.filter(x => x.address !== a.address)
  })
}

const recheck = () => step('refresh', async () => {
  const r = await call<List & { errors: number }>('refresh')
  data.value = r
  toast(r.errors ? t('aliases.checkedErr', { n: r.errors }) : t('aliases.checked'), { tone: r.errors ? 'warn' : 'ok' })
})

const importing = ref(false)
const pasted = ref('')
const doImport = () => step('import', async () => {
  const r = await call<List & { added: number }>('import', { text: pasted.value })
  data.value = r
  pasted.value = ''
  importing.value = false
  toast(t('aliases.imported', { n: r.added }), { tone: 'ok' })
})
</script>

<template>
  <div>
    <h2 class="sec">{{ $t('aliases.title') }}</h2>
    <div v-if="error" class="errbox">{{ error.statusMessage || error.message }}</div>
    <Skeleton v-else-if="!data" kind="rows" :n="5" />
    <template v-else>
      <Panel v-if="!data.signed_in" :title="$t('aliases.signIn')">
        <form v-if="!data.pending" class="line" @submit.prevent="login">
          <input v-model="user" :placeholder="$t('aliases.userPh')" autocomplete="username" autocapitalize="off">
          <button class="btn primary" :disabled="!user.trim() || busy === 'login'">{{ $t('aliases.sendCode') }}</button>
        </form>
        <template v-else>
          <p class="muted small">{{ $t('aliases.codeSent', { u: data.pending }) }}</p>
          <form class="line" @submit.prevent="verify">
            <input v-model="otp" :placeholder="$t('aliases.codePh')" autocomplete="one-time-code" autocapitalize="off">
            <button class="btn primary" :disabled="!otp.trim() || busy === 'verify'">{{ $t('aliases.verify') }}</button>
          </form>
          <button class="lnk small" @click="logout">{{ $t('aliases.otherUser') }}</button>
        </template>
      </Panel>

      <Panel v-else :title="$t('aliases.new')" :sub="`${data.user}@duck.com`">
        <template #actions>
          <button class="lnk small" @click="logout">{{ $t('aliases.signOut') }}</button>
        </template>
        <form class="line" @submit.prevent="make">
          <input v-model="label" :placeholder="$t('aliases.labelPh')">
          <button class="btn primary" :disabled="busy === 'new'">{{ $t('aliases.generate') }}</button>
        </form>
        <p v-if="fresh" class="fresh"><span class="mono">{{ fresh }}</span> <button class="btn sm ghost" @click="copy(fresh)"><Icon name="copy" :size="13" /></button></p>
      </Panel>

      <Panel :title="$t('aliases.yours')" :sub="String(counts.all)">
        <template #actions>
          <button class="btn sm ghost" @click="importing = !importing">{{ $t('aliases.import') }}</button>
          <button v-if="data.signed_in && counts.all" class="btn sm ghost" :disabled="busy === 'refresh'" @click="recheck">
            <Icon name="refresh" :size="13" /> {{ busy === 'refresh' ? $t('aliases.checking') : $t('aliases.check') }}
          </button>
        </template>
        <div v-if="importing" class="imp">
          <textarea v-model="pasted" rows="5" :placeholder="$t('aliases.importPh')" />
          <button class="btn primary sm" :disabled="!pasted.trim() || busy === 'import'" @click="doImport">{{ $t('aliases.add') }}</button>
        </div>
        <div class="line">
          <input v-model="q" type="search" :placeholder="$t('aliases.searchPh')">
        </div>
        <div class="chips">
          <button v-for="k in (['all', 'on', 'off'] as const)" :key="k" class="chip" :class="{ on: show === k }" @click="show = k">
            {{ $t(`aliases.f_${k}`) }} {{ counts[k] }}
          </button>
        </div>
        <p v-if="!list.length" class="empty-state">{{ counts.all ? $t('aliases.noMatch') : $t('aliases.empty') }}</p>
        <ul v-else class="rows">
          <li v-for="a in list" :key="a.address" :class="{ off: a.active === false }">
            <div class="top">
              <button class="addr mono" @click="copy(a.address)">{{ a.address }}</button>
              <span v-if="a.active === false" class="pill bad">{{ $t('aliases.off') }}</span>
              <span v-else-if="a.active === null" class="pill">{{ $t('aliases.unknown') }}</span>
            </div>
            <template v-if="editing === a.address">
              <input v-model="draft.label" :placeholder="$t('aliases.labelPh')">
              <input v-model="draft.note" :placeholder="$t('aliases.notePh')">
              <div class="acts">
                <button class="btn sm primary" :disabled="busy === `e:${a.address}`" @click="save(a)">{{ $t('aliases.save') }}</button>
                <button class="btn sm ghost" @click="editing = ''">{{ $t('aliases.cancel') }}</button>
              </div>
            </template>
            <template v-else>
              <div class="meta">
                <b v-if="a.label">{{ a.label }}</b><span v-else class="faint">{{ $t('aliases.noLabel') }}</span>
                <span class="faint small">· {{ fmtDate(a.created * 1000) }}</span>
              </div>
              <p v-if="a.note" class="muted small">{{ a.note }}</p>
              <div class="acts">
                <button class="btn sm ghost" @click="copy(a.address)"><Icon name="copy" :size="13" /> {{ $t('aliases.copy') }}</button>
                <button class="btn sm ghost" @click="edit(a)">{{ $t('aliases.edit') }}</button>
                <button v-if="data.signed_in" class="btn sm ghost" @click="toggle(a)">{{ a.active === false ? $t('aliases.turnOn') : $t('aliases.turnOff') }}</button>
                <button class="btn sm ghost danger" :class="{ sure: armed === `d:${a.address}` }" :disabled="busy === `d:${a.address}`" @click="remove(a)">
                  {{ armed === `d:${a.address}` ? $t('aliases.sure') : $t('aliases.delete') }}
                </button>
              </div>
            </template>
          </li>
        </ul>
      </Panel>
    </template>
  </div>
</template>

<style scoped>
.panel + .panel { margin-top: 14px; }
.line { display: flex; gap: 8px; margin-bottom: 10px; }
.line input { flex: 1; min-width: 0; }
.fresh { display: flex; align-items: center; gap: 8px; margin: 4px 0 0; color: var(--ok); }
.imp { display: grid; gap: 8px; margin-bottom: 12px; justify-items: start; }
.imp textarea { width: 100%; }
.chips { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
.rows { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
.rows li { border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 10px 12px; display: grid; gap: 6px; background: var(--panel-2); }
.rows li.off { opacity: .6; }
.top { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.addr { background: none; border: 0; padding: 0; color: var(--text); font-size: 13px; cursor: pointer; text-align: left; word-break: break-all; }
.meta { display: flex; gap: 6px; align-items: baseline; flex-wrap: wrap; }
.acts { display: flex; gap: 6px; flex-wrap: wrap; }
@media (pointer: coarse) { .acts .btn { min-height: 32px; } }
</style>
