<script setup lang="ts">
/** Mail -> Categories: the owner's categories with their rules, auto-suggest, and re-sorting of cached mail with the local model. */
const emit = defineEmits<{ (e: 'changed'): void }>()

const data = ref<any | null>(null)
const error = ref('')
const note = ref('')
const { armed, arm } = useArm()
const { toast, optimistic } = useToast()
const errText = (e: any) => e?.data?.statusMessage || e?.data?.message || e?.message || 'failed'

async function load() {
  try { data.value = await $fetch<any>('/api/mail/categories'); error.value = '' }
  catch (e: any) { error.value = errText(e) }
}
await load()
const cats = computed<any[]>(() => data.value?.categories ?? [])
const colors = computed<string[]>(() => data.value?.colors ?? ['accent', 'ok', 'warn', 'bad', 'claude', 'muted', 'faint', 'text'])
const post = (path: string, body: any) => $fetch<any>('/api/mail/' + path, { method: 'POST', body: { ...body, confirm: true } })

// ---- enable / disable ----
function toggle(c: any) {
  optimistic(() => { c.enabled = !c.enabled }, () => { c.enabled = !c.enabled },
    async () => { await post('categories-save', { id: c.id, name: c.name, color: c.color, description: c.description, enabled: c.enabled }); emit('changed') }, 'Category')
}

// ---- edit form ----
const blank = () => ({ id: '', name: '', color: 'accent', description: '' })
const f = reactive(blank())
const editing = ref(false)
const cur = computed(() => cats.value.find(c => c.id === f.id))
const busy = ref('')
const formErr = ref('')
const rule = reactive({ kind: 'domain', value: '', apply: true })
const KINDS = [{ k: 'domain', t: 'Domain' }, { k: 'from', t: 'Sender' }, { k: 'subject', t: 'Subject' }]
const kindLabel = (k: string) => KINDS.find(x => x.k === k)?.t ?? k

function startNew() { Object.assign(f, blank()); formErr.value = ''; rule.value = ''; editing.value = true }
function startEdit(c: any) { Object.assign(f, { id: c.id, name: c.name, color: c.color, description: c.description }); formErr.value = ''; rule.value = ''; editing.value = true }
async function save() {
  busy.value = 'save'; formErr.value = ''
  try {
    const r = await post('categories-save', { id: f.id, name: f.name, color: f.color, description: f.description })
    f.id = r.id; await load(); emit('changed'); editing.value = false
  } catch (e: any) { formErr.value = errText(e) } finally { busy.value = '' }
}
async function remove() {
  if (!arm('del' + f.id)) return
  try { const r = await post('categories-delete', { id: f.id }); toast(`Category removed, ${r.moved} moved to Other`); editing.value = false; await load(); emit('changed') }
  catch (e: any) { formErr.value = errText(e) }
}
async function addRule() {
  busy.value = 'rule'; formErr.value = ''
  try {
    const r = await post('categories-rule', { category: f.id, kind: rule.kind, value: rule.value, apply: rule.apply })
    rule.value = ''; await load(); emit('changed')
    toast(r.applied ? `Rule added, ${r.applied} mails moved` : 'Rule added')
  } catch (e: any) { formErr.value = errText(e) } finally { busy.value = '' }
}
async function removeRule(r: any) {
  if (!arm('rule' + r.id)) return
  try { await post('categories-rule-delete', { id: r.id }); await load() } catch (e: any) { formErr.value = errText(e) }
}

// ---- suggestions ----
const sugg = ref<any[]>([])
const suggesting = ref(false)
async function suggest() {
  suggesting.value = true; error.value = ''
  try {
    sugg.value = (await $fetch<any>('/api/mail/categories-suggest', { method: 'POST' })).suggestions
    if (!sugg.value.length) note.value = 'No new ideas right now.'
  } catch (e: any) { error.value = errText(e) } finally { suggesting.value = false }
}
async function accept(s: any) {
  try {
    await post('categories-save', { name: s.name, color: colors.value[(cats.value.length + 1) % colors.value.length], description: s.description })
    sugg.value = sugg.value.filter(x => x !== s); await load(); emit('changed')
  } catch (e: any) { error.value = errText(e) }
}

// ---- re-sort ----
const sortOpen = ref(false)
const scope = ref<'all' | 'unsure'>('all')
const sorting = ref(false)
const progress = ref('')
async function resort() {
  sorting.value = true; error.value = ''; note.value = ''
  try {
    const r = await post('categories-resort', { only_unsure: scope.value === 'unsure' })
    const total = r.count
    progress.value = `Sorting ${total} mails…`
    const out = await drainTriage('', 200, (left) => { progress.value = `Sorting… ${Math.max(0, total - left)} of ${total} done` })
    progress.value = ''
    note.value = out.left ? `Stopped with ${out.left} left${out.note ? ': ' + out.note : ''}` : `Sorted ${total} mails.`
    sortOpen.value = false
  } catch (e: any) { error.value = errText(e); progress.value = '' } finally { sorting.value = false; await load(); emit('changed') }
}
</script>

<template>
  <div class="cats">
    <p v-if="error" class="errbox">{{ error }}</p>
    <p v-if="note" class="faint small">{{ note }}</p>

    <div class="row">
      <button type="button" class="btn primary" @click="startNew"><Icon name="plus" :size="16" /> New category</button>
      <button type="button" class="btn" :disabled="suggesting" @click="suggest"><Icon name="sparkles" :size="16" /> {{ suggesting ? 'Thinking…' : 'Suggest categories' }}</button>
      <button type="button" class="btn" :disabled="sorting" @click="sortOpen = !sortOpen"><Icon name="refresh-cw" :size="16" /> Re-sort mail</button>
    </div>

    <Panel v-if="sortOpen || sorting" title="Re-sort mail" id="mail-cat-resort">
      <div class="seg">
        <button type="button" :class="{ on: scope === 'all' }" :disabled="sorting" @click="scope = 'all'">All auto-sorted</button>
        <button type="button" :class="{ on: scope === 'unsure' }" :disabled="sorting" @click="scope = 'unsure'">Only unsure</button>
      </div>
      <p class="faint small">Mail you sorted by hand stays where it is.</p>
      <div class="row">
        <button type="button" class="btn primary" :disabled="sorting" @click="resort">{{ sorting ? 'Sorting…' : 'Start' }}</button>
        <button v-if="!sorting" type="button" class="btn ghost" @click="sortOpen = false">Cancel</button>
        <span v-if="progress" class="small muted">{{ progress }}</span>
      </div>
    </Panel>

    <Panel v-if="sugg.length" title="Suggestions" id="mail-cat-sugg">
      <div class="sugg">
        <div v-for="s in sugg" :key="s.name" class="sg">
          <b>{{ s.name }}</b>
          <span class="muted small">{{ s.description }}</span>
          <div class="row">
            <button type="button" class="btn sm primary" @click="accept(s)">Accept</button>
            <button type="button" class="btn sm ghost" @click="sugg = sugg.filter(x => x !== s)">Dismiss</button>
          </div>
        </div>
      </div>
    </Panel>

    <Panel v-if="editing" :title="f.id ? 'Edit category' : 'New category'" id="mail-cat-edit">
      <form class="form" @submit.prevent="save">
        <label>Name<input v-model="f.name" maxlength="30" autocomplete="off"></label>
        <div class="lbl">Colour</div>
        <div class="row">
          <button v-for="c in colors" :key="c" type="button" class="chip" :class="{ on: f.color === c }" :style="{ '--c': `var(--${c})` }" @click="f.color = c">
            <span class="sw" />{{ c }}
          </button>
        </div>
        <label>What belongs here (for the model)<textarea v-model="f.description" rows="3" maxlength="200" /></label>
        <span class="faint small">{{ f.description.length }} / 200</span>

        <template v-if="f.id">
          <div class="lbl">Rules (checked first, no model needed)</div>
          <p v-if="!cur?.rules.length" class="faint small">No rules yet.</p>
          <div v-for="r in cur?.rules" :key="r.id" class="rl">
            <span class="small"><span class="faint">{{ kindLabel(r.kind) }}</span> {{ r.value }}</span>
            <button type="button" class="btn sm danger" :class="{ sure: armed === 'rule' + r.id }" @click="removeRule(r)">{{ armed === 'rule' + r.id ? 'Sure?' : 'Remove' }}</button>
          </div>
          <div class="seg">
            <button v-for="k in KINDS" :key="k.k" type="button" :class="{ on: rule.kind === k.k }" @click="rule.kind = k.k">{{ k.t }}</button>
          </div>
          <input v-model="rule.value" :placeholder="rule.kind === 'domain' ? 'example.com' : rule.kind === 'from' ? 'part of the address' : 'words in the subject'" autocapitalize="off" autocomplete="off">
          <label class="chk"><input v-model="rule.apply" type="checkbox"> Also move matching mail now</label>
          <div class="row"><button type="button" class="btn sm" :disabled="rule.value.trim().length < 2 || busy === 'rule'" @click="addRule">Add rule</button></div>
        </template>

        <p v-if="formErr" class="errbox">{{ formErr }}</p>
        <div class="row">
          <button type="submit" class="btn primary" :disabled="!f.name.trim() || busy === 'save'">{{ busy === 'save' ? 'Saving…' : 'Save' }}</button>
          <button type="button" class="btn ghost" @click="editing = false">Cancel</button>
          <button v-if="f.id && cur && !cur.builtin" type="button" class="btn danger" :class="{ sure: armed === 'del' + f.id }" @click="remove">{{ armed === 'del' + f.id ? 'Sure?' : 'Delete' }}</button>
        </div>
      </form>
    </Panel>

    <Skeleton v-if="!data" kind="cards" />
    <Panel v-for="c in cats" :key="c.id" :id="'mail-cat-' + c.id" :title="c.name" :sub="c.description" fold="open">
      <div class="meta">
        <MailCatPill :name="c.name" :color="c.color" />
        <span class="faint small">{{ c.count }} mails, {{ c.unread }} unread</span>
        <span class="faint small">{{ c.rules.length }} {{ c.rules.length === 1 ? 'rule' : 'rules' }}</span>
        <span v-if="c.builtin" class="faint small">Built-in</span>
      </div>
      <div class="row">
        <button type="button" class="chip" :class="{ on: c.enabled }" :disabled="c.id === 'other'" @click="toggle(c)">{{ c.enabled ? 'Enabled' : 'Off' }}</button>
        <button type="button" class="btn sm" @click="startEdit(c)">Edit</button>
      </div>
    </Panel>
  </div>
</template>

<style scoped>
.cats { display: flex; flex-direction: column; gap: 10px; }
.row, .meta { display: flex; flex-wrap: wrap; gap: 8px 10px; align-items: center; }
.row { margin-top: 4px; }
.errbox { margin: 0; }
.form { display: flex; flex-direction: column; gap: 10px; }
.form label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: var(--muted); }
.form label.chk { flex-direction: row; align-items: center; gap: 8px; min-height: 36px; }
.form input:not([type='checkbox']), .form textarea { width: 100%; box-sizing: border-box; font: inherit; min-height: 36px; }
.lbl { font-size: 13px; color: var(--muted); }
.sw { width: 10px; height: 10px; border-radius: 50%; background: var(--c); flex: none; }
.rl { display: flex; align-items: center; justify-content: space-between; gap: 8px 10px; flex-wrap: wrap; }
.sugg { display: flex; flex-direction: column; gap: 12px; }
.sg { display: flex; flex-direction: column; gap: 4px; }
@media (pointer: coarse) { .btn.sm, .chip, .seg > button { min-height: 36px; } }
</style>
