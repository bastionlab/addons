<script setup lang="ts">
// public links to a project's preview (dash-share behind Tailscale Funnel): single use, expiry, or until revoked
const props = defineProps<{ box: any, p: any }>()

const ports = computed<number[]>(() => [...new Set<number>([...(props.p.ports ?? []), ...(props.p.urls ?? []).map((u: any) => u.port)])])
const port = ref<number | null>(null)
watchEffect(() => { if (!port.value || !ports.value.includes(port.value)) port.value = ports.value[0] ?? null })
const ttl = ref(86400)
const once = ref(false)
const TTLS = [[3600, '1 hour'], [86400, '1 day'], [7 * 86400, '7 days'], [0, 'until revoked']] as const

const { data, refresh } = useFetch<any>('/api/shares', { key: 'shares', default: () => ({ links: [] }) })
const mine = computed(() => (data.value?.links ?? []).filter((l: any) => l.project?.vmid === props.box.vmid && l.project?.path === props.p.path))
const busy = ref(false)
const error = ref('')
const copied = ref('')

async function create() {
  busy.value = true
  error.value = ''
  try {
    const l: any = await $fetch('/api/shares', { method: 'POST', body: { vmid: props.box.vmid, path: props.p.path, port: port.value, ttl: ttl.value, once: once.value } })
    await refresh()
    copy(`${data.value.base}/s/${l.token}`, l.id)
  } catch (e: any) {
    error.value = e?.data?.statusMessage || e?.message
  } finally { busy.value = false }
}
async function act(action: 'revoke' | 'delete', id: string) {
  await $fetch(`/api/shares/${action}`, { method: 'POST', body: { id } }).catch((e: any) => { error.value = e?.data?.statusMessage || e?.message })
  refresh()
}
function copy(url: string, id: string) {
  navigator.clipboard?.writeText(url)
  copied.value = id
  setTimeout(() => copied.value === id && (copied.value = ''), 1500)
}
const left = (l: any) => l.expires ? `ends ${new Date(l.expires).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}` : 'no expiry'
</script>

<template>
  <div class="share">
    <div v-if="data && data.funnel === false" class="small warn">
      Public access is off: Tailscale Funnel isn't serving :8443 yet, so links won't open for anyone.
    </div>
    <div v-if="!ports.length" class="small faint">No port known for this project. Start the preview once or set <code>ports:</code> in .dashboard.yml.</div>
    <div v-else class="form">
      <select v-if="ports.length > 1" v-model="port" title="port"><option v-for="x in ports" :key="x" :value="x">:{{ x }}</option></select>
      <select v-model="ttl" title="expires after"><option v-for="[s, t] in TTLS" :key="s" :value="s">{{ t }}</option></select>
      <label class="small once"><input v-model="once" type="checkbox"> one visit</label>
      <button class="btn primary" :disabled="busy" @click="create">{{ busy ? '…' : 'Create link' }}</button>
    </div>
    <div v-if="error" class="small bad">{{ error }}</div>
    <div v-for="l in mine" :key="l.id" class="link small" :class="{ off: l.status !== 'active' }">
      <span class="pill" :class="l.status === 'active' ? 'ok' : ''">{{ l.status }}</span>
      <span class="faint meta">:{{ l.project.port }} · {{ l.once ? 'one visit' : left(l) }} · {{ l.uses }} open{{ l.uses === 1 ? '' : 's' }}</span>
      <button v-if="l.status === 'active'" class="btn ghost sm" @click="copy(l.url, l.id)">{{ copied === l.id ? 'Copied' : 'Copy' }}</button>
      <button v-if="!l.revoked" class="btn ghost sm danger" @click="act('revoke', l.id)">Revoke</button>
      <button v-else class="btn ghost sm" title="remove from the list" @click="act('delete', l.id)" aria-label="remove"><Icon name="x" :size="16"/></button>
    </div>
  </div>
</template>

<style scoped>
.share { display: flex; flex-direction: column; gap: 6px; padding: 8px 10px; border: 1px solid var(--line); border-radius: var(--radius-sm); background: var(--panel-2); }
.form { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.form select { padding: 4px 6px; }
.once { display: flex; align-items: center; gap: 4px; }
.link { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.link.off { opacity: .6; }
.meta { flex: 1; min-width: 0; }
.warn { color: var(--warn); }
@media (pointer: coarse) { .form select, .link .btn { min-height: 34px; } }
</style>
