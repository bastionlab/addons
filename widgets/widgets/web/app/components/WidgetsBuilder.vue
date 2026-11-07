<script setup lang="ts">
import { BUTTON_TARGETS, cleanWidget, WIDGET_LOOKS, WIDGET_SIZES, WIDGET_SOURCES, WidgetError, type WidgetDef, type WidgetLook } from '../utils/widgets'
import type { WidgetsApi } from '../composables/useWidgets'

/**
 * The builder sheet (Home edit mode): My widgets / Library / Create. Create is a form for the declarative schema,
 * or a sentence for Claude (same job mechanism as Designs' "Describe a look"); the preview is the real widget and
 * nothing is stored before Save.
 */
const props = defineProps<{ api: WidgetsApi, packs: string[], page?: boolean }>()
const emit = defineEmits<{ close: [] }>()
const { t } = useI18n()
const { toast } = useToast()
const { armed, arm } = useArm()
const tab = ref<'mine' | 'library' | 'create'>('mine')

// ---- library: widget packs (add-ons with kind: widget)
interface Pack { pack: string, name: string, version: string, defs: WidgetDef[], errors: string[] }
const lib = ref<Pack[] | null>(null)
const libErr = ref('')
async function loadLib() {
  try { lib.value = (await $fetch<{ packs: Pack[] }>('/api/widgets/library')).packs } catch (e: any) { libErr.value = e?.data?.statusMessage || 'failed' }
}
function addFromPack(d: WidgetDef) {
  try { props.api.save(d) } catch { toast(t('widgets.limit'), { tone: 'bad' }) }
}

// ---- sources to pick from
const opts = ref<{ services: string[], tasks: { id: string, title: string }[], notes: { id: number, title: string }[] }>({ services: [], tasks: [], notes: [] })
onMounted(() => {
  loadLib()
  $fetch<typeof opts.value>('/api/widgets/sources').then(r => (opts.value = r)).catch(() => {})
})

// ---- the form
const blank = () => ({
  id: '', name: '', size: 'S', look: 'number' as WidgetLook, stype: 'metric', path: '/api/', pick: '', sname: '', sid: '',
  prefix: '', suffix: '', decimals: '', max: '', field: '', bpath: '/api/chat-tasks', blabel: '', btask: '',
})
const f = reactive(blank())
const editingId = ref('')
const ask = ref('')
const aiBusy = ref(false)
const aiErr = ref('')

const raw = computed(() => ({
  id: f.id || 'preview', name: f.name || t('widgets.untitled'), size: f.size, look: f.look,
  source: f.look === 'button' ? { type: 'none' } : { type: f.stype, path: f.path, pick: f.pick, name: f.sname, id: f.sid },
  format: { prefix: f.prefix, suffix: f.suffix, decimals: f.decimals, max: f.max, field: f.field },
  button: { label: f.blabel, path: f.bpath, body: f.bpath === '/api/chat-tasks' ? { op: 'run', id: f.btask } : {} },
}))
const checked = computed<{ def?: WidgetDef, error?: string }>(() => {
  try { return { def: cleanWidget(raw.value) } } catch (e: any) { return { error: e instanceof WidgetError ? e.message : String(e.message) } }
})
// the preview only refetches when the cleaned definition changes
const preview = ref<WidgetDef | null>(null)
let tm: any
watch(checked, (c) => { clearTimeout(tm); tm = setTimeout(() => (preview.value = c.def ?? null), 500) }, { immediate: true })

function load(d: WidgetDef) {
  Object.assign(f, blank(), {
    id: d.id, name: d.name, size: d.size, look: d.look, stype: d.source.type === 'none' ? 'metric' : d.source.type, path: d.source.path ?? '/api/',
    pick: d.source.pick ?? '', sname: d.source.name ?? '', sid: d.source.id ?? '',
    prefix: d.format?.prefix ?? '', suffix: d.format?.suffix ?? '', decimals: d.format?.decimals ?? '', max: d.format?.max ?? '', field: d.format?.field ?? '',
    bpath: d.button?.path ?? '/api/chat-tasks', blabel: d.button?.label ?? '', btask: d.button?.body?.id ?? '',
  })
  editingId.value = d.id
  tab.value = 'create'
}
function fresh() { Object.assign(f, blank()); editingId.value = ''; ask.value = ''; aiErr.value = ''; tab.value = 'create' }
const slug = (n: string) => `${n.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 30) || 'widget'}-${Math.random().toString(36).slice(2, 6)}`

function save() {
  const c = checked.value
  if (!c.def) return
  const def = { ...c.def, id: editingId.value || slug(c.def.name) }
  try { props.api.save(def) } catch { return toast(t('widgets.limit'), { tone: 'bad' }) }
  toast(t('widgets.saved', { name: def.name }))
  tab.value = 'mine'
}

async function describe() {
  if (!ask.value.trim() || aiBusy.value) return
  aiBusy.value = true; aiErr.value = ''
  try {
    const id = editingId.value || slug(f.name || 'widget')
    const { job } = await $fetch<{ job: string }>('/api/widgets/ai', { method: 'POST', body: { ask: ask.value, base: checked.value.def, id } })
    for (let i = 0; i < 150; i++) {
      await new Promise(r => setTimeout(r, 2000))
      const r = await $fetch<any>('/api/widgets/ai', { query: { job, id } })
      if (r.state === 'done') { load(r.widget); return }
      if (r.state === 'failed' || r.state === 'gone') throw new Error(r.error || 'failed')
    }
    throw new Error('timed out')
  } catch (e: any) { aiErr.value = e?.data?.statusMessage || e?.message || 'failed' }
  finally { aiBusy.value = false }
}

const home = computed(() => props.api.placed.value)
const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') emit('close') }
onMounted(() => document.addEventListener('keydown', onKey))
onUnmounted(() => document.removeEventListener('keydown', onKey))
const lookNeedsFormat = computed(() => f.look !== 'button')
</script>

<template>
  <Teleport to="body" :disabled="page">
    <div class="bk" :class="{ pg: page }" @click.self="emit('close')">
      <div class="sh" role="dialog" :aria-label="t('widgets.title')">
        <div class="top">
          <b>{{ t('widgets.title') }}</b>
          <button type="button" class="btn sm ghost" @click="emit('close')">{{ t('widgets.close') }}</button>
        </div>
        <div class="seg">
          <button v-for="x in (['mine', 'library', 'create'] as const)" :key="x" type="button" :class="{ on: tab === x }" @click="x === 'create' ? fresh() : (tab = x)">{{ t(`widgets.tab.${x}`) }}</button>
        </div>

        <div v-if="tab === 'mine'" class="body">
          <div v-if="!api.list.value.length" class="empty-state">{{ t('widgets.nothingYet') }}</div>
          <div v-for="w in api.list.value" :key="w.id" class="row">
            <div class="rt">
              <div>{{ w.name }}</div>
              <div class="muted small">{{ w.size }} · {{ t(`widgets.look.${w.look}`) }}</div>
            </div>
            <span v-if="api.has(w.id)" class="pill ok">{{ t('widgets.onHome') }}</span>
            <button v-if="api.has(w.id)" type="button" class="btn sm ghost" :aria-label="t('widgets.up')" @click="api.move(w.id, -1)">{{ t('widgets.up') }}</button>
            <button v-if="api.has(w.id)" type="button" class="btn sm ghost" :aria-label="t('widgets.down')" @click="api.move(w.id, 1)">{{ t('widgets.down') }}</button>
            <button type="button" class="btn sm" @click="api.toggle(w.id)">{{ api.has(w.id) ? t('widgets.hide') : t('widgets.show') }}</button>
            <button v-if="w.look !== 'component'" type="button" class="btn sm" @click="load(w)">{{ t('widgets.editOne') }}</button>
            <button type="button" class="btn sm" :class="{ danger: armed === w.id }" @click="arm(w.id) && api.remove(w.id)">{{ armed === w.id ? t('widgets.sure') : t('widgets.delete') }}</button>
          </div>
        </div>

        <div v-else-if="tab === 'library'" class="body">
          <Skeleton v-if="!lib && !libErr" kind="rows" />
          <div v-else-if="libErr" class="errbox">{{ libErr }}</div>
          <div v-else-if="!lib?.length" class="empty-state">{{ t('widgets.noPacks') }}</div>
          <Panel v-for="p in lib" :key="p.pack" :title="p.name" :sub="`v${p.version}`" :id="`widgets-pack-${p.pack}`">
            <div v-for="d in p.defs" :key="d.id" class="row">
              <div class="rt">
                <div>{{ d.name }}</div>
                <div class="muted small">{{ d.size }} · {{ t(`widgets.look.${d.look}`) }}</div>
              </div>
              <button v-if="!home.includes(d.id)" type="button" class="btn sm primary" @click="addFromPack(d)">{{ t('widgets.addHome') }}</button>
              <span v-else class="pill ok">{{ t('widgets.onHome') }}</span>
            </div>
            <div v-for="e in p.errors" :key="e" class="bad small">{{ e }}</div>
          </Panel>
        </div>

        <div v-else class="body">
          <div class="ai">
            <label class="small muted" for="wd-ask">{{ t('widgets.describe') }}</label>
            <textarea id="wd-ask" v-model="ask" rows="2" :placeholder="t('widgets.describePh')" />
            <div class="line">
              <button type="button" class="btn sm" :disabled="aiBusy || !ask.trim()" @click="describe">{{ aiBusy ? t('widgets.asking') : t('widgets.ask') }}</button>
              <span v-if="aiErr" class="bad small">{{ aiErr }}</span>
            </div>
          </div>

          <div class="form">
            <label>{{ t('widgets.f.name') }}<input v-model="f.name" maxlength="40"></label>
            <div class="seg">
              <button v-for="s in WIDGET_SIZES" :key="s" type="button" :class="{ on: f.size === s }" @click="f.size = s">{{ s }}</button>
            </div>
            <label>{{ t('widgets.f.look') }}
              <select v-model="f.look"><option v-for="l in WIDGET_LOOKS" :key="l" :value="l">{{ t(`widgets.look.${l}`) }}</option></select>
            </label>

            <template v-if="f.look !== 'button'">
              <label>{{ t('widgets.f.source') }}
                <select v-model="f.stype"><option v-for="s in WIDGET_SOURCES" :key="s" :value="s">{{ t(`widgets.src.${s}`) }}</option></select>
              </label>
              <label v-if="f.stype === 'api'">{{ t('widgets.f.path') }}<input v-model="f.path" class="mono" autocapitalize="off" spellcheck="false"></label>
              <label v-if="f.stype === 'api' || f.stype === 'metric'">{{ t(f.stype === 'metric' ? 'widgets.f.metric' : 'widgets.f.pick') }}
                <input v-model="f.pick" class="mono" :placeholder="f.stype === 'metric' ? 'host.cpu' : 'data.items[0].value'" autocapitalize="off" spellcheck="false">
              </label>
              <label v-if="f.stype === 'service'">{{ t('widgets.f.service') }}
                <select v-model="f.sname"><option value="">-</option><option v-for="s in opts.services" :key="s" :value="s">{{ s }}</option></select>
              </label>
              <label v-if="f.stype === 'task'">{{ t('widgets.f.task') }}
                <select v-model="f.sid"><option value="">-</option><option v-for="x in opts.tasks" :key="x.id" :value="x.id">{{ x.title }}</option></select>
              </label>
              <label v-if="f.stype === 'note'">{{ t('widgets.f.note') }}
                <select v-model="f.sid"><option value="">-</option><option v-for="x in opts.notes" :key="x.id" :value="String(x.id)">{{ x.title }}</option></select>
              </label>
            </template>
            <template v-else>
              <label>{{ t('widgets.f.action') }}
                <select v-model="f.bpath"><option v-for="(_, p) in BUTTON_TARGETS" :key="p" :value="p">{{ t(`widgets.act.${p === '/api/chat-tasks' ? 'task' : 'speedtest'}`) }}</option></select>
              </label>
              <label v-if="f.bpath === '/api/chat-tasks'">{{ t('widgets.f.task') }}
                <select v-model="f.btask"><option value="">-</option><option v-for="x in opts.tasks" :key="x.id" :value="x.id">{{ x.title }}</option></select>
              </label>
              <label>{{ t('widgets.f.label') }}<input v-model="f.blabel" maxlength="30"></label>
            </template>

            <div v-if="lookNeedsFormat" class="two">
              <label>{{ t('widgets.f.prefix') }}<input v-model="f.prefix" maxlength="12"></label>
              <label>{{ t('widgets.f.suffix') }}<input v-model="f.suffix" maxlength="12"></label>
              <label>{{ t('widgets.f.decimals') }}<input v-model="f.decimals" inputmode="numeric"></label>
              <label v-if="f.look === 'gauge'">{{ t('widgets.f.max') }}<input v-model="f.max" inputmode="decimal"></label>
              <label v-if="f.look === 'list' || f.look === 'sparkline'">{{ t('widgets.f.field') }}<input v-model="f.field" class="mono" autocapitalize="off"></label>
            </div>
          </div>

          <div class="pv">
            <div class="small muted">{{ t('widgets.preview') }}</div>
            <div v-if="checked.error" class="bad small">{{ checked.error }}</div>
            <div v-else-if="preview" class="pvbox" :class="`sz-${preview.size}`"><WidgetView :def="preview" :packs="packs" preview /></div>
          </div>
          <div class="line">
            <button type="button" class="btn primary" :disabled="!checked.def" @click="save">{{ t('widgets.save') }}</button>
            <button type="button" class="btn ghost" @click="tab = 'mine'">{{ t('widgets.cancel') }}</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.bk.pg { position: static; background: none; display: block; }
.bk.pg .sh { max-height: none; border: 1px solid var(--line); border-radius: var(--radius); max-width: none; }
.bk { position: fixed; inset: 0; z-index: 90; background: color-mix(in srgb, var(--bg) 70%, transparent); display: flex; align-items: flex-end; justify-content: center; }
.sh { width: 100%; max-width: 640px; max-height: 92dvh; overflow: auto; background: var(--panel); border: 1px solid var(--line-2); border-radius: var(--radius) var(--radius) 0 0; padding: 14px; display: flex; flex-direction: column; gap: 12px; }
@media (min-width: 641px) { .bk { align-items: center; } .sh { border-radius: var(--radius); } }
.top { display: flex; justify-content: space-between; align-items: center; }
.body { display: flex; flex-direction: column; gap: 10px; }
.row { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; padding: 8px 0; border-bottom: 1px solid var(--line); }
.rt { flex: 1 1 140px; min-width: 0; }
.form, .ai { display: flex; flex-direction: column; gap: 8px; }
label { display: flex; flex-direction: column; gap: 3px; font-size: 12px; color: var(--muted); }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.line { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.pvbox { height: 104px; }
.pvbox.sz-M { height: 104px; }
.pvbox.sz-L { height: 216px; }
.pvbox.sz-S { width: 50%; min-width: 150px; }
@media (pointer: coarse) { .sh .btn.sm { min-height: 36px; } }
</style>
