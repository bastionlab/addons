<script setup lang="ts">
// what fits the GPU (live catalogue, ranked) + what is installed; pull and delete are approve-then-run actions
const { t } = useI18n()
const { run } = useActions()
const { arm, armed } = useArm()
const ctx = ref(8192)
const cat = ref<any>(null)
const disk = ref<any>(null)
const error = ref('')

async function load() {
  try {
    const [c, d] = await Promise.all([$fetch<any>('/api/ai/cookbook/catalogue', { query: { ctx: ctx.value } }), $fetch<any>('/api/ai/disk')])
    cat.value = c
    disk.value = d
    error.value = ''
  } catch (e: any) { error.value = e?.data?.statusMessage || e?.message || 'error' }
}
onMounted(load)
watch(ctx, load)

const have = computed(() => new Set((disk.value?.models ?? []).map((m: any) => m.name)))
const isIn = (m: string) => have.value.has(m) || have.value.has(`${m}:latest`)
const tone = (v: string) => (v === 'fits' ? 'ok' : v === 'partial' ? 'warn' : 'bad')
const pull = (model: string) => run('ollama_pull', { model }, load)
function del(model: string) {
  if (!arm(model)) return
  run('ollama_delete', { model }, load)
}
</script>

<template>
  <div class="grid">
    <div v-if="error" class="errbox">{{ error }}</div>

    <Panel :title="$t('ai.installed')" :sub="disk ? $t('ai.installedSub', { n: disk.models.length, size: bytes(disk.models_bytes) }) : ''">
      <Skeleton v-if="!disk" kind="rows" :n="3" />
      <template v-else>
        <div v-for="m in disk.models" :key="m.name" class="mrow">
          <div class="grow">
            <span class="mono name">{{ m.name }}</span>
            <span v-if="m.uncensored" class="pill">{{ $t('ai.uncensored') }}</span>
          </div>
          <span class="muted small num">{{ bytes(m.size) }}</span>
          <button class="btn sm danger" :class="{ sure: armed === m.name }" @click="del(m.name)">{{ armed === m.name ? $t('ai.sure') : $t('ai.delete') }}</button>
        </div>
        <p class="muted small">{{ $t('ai.disk', { used: bytes(disk.disk.used), free: bytes(disk.disk.free), total: bytes(disk.disk.total) }) }}</p>
      </template>
    </Panel>

    <Panel :title="$t('ai.cookbookTitle')" :sub="cat ? $t('ai.cookbookSub', { vram: cat.vram_gb, usable: cat.usable_gb, ctx: cat.ctx }) : ''">
      <div class="seg ctx">
        <button v-for="c in [4096, 8192, 16384, 32768]" :key="c" :class="{ on: ctx === c }" @click="ctx = c">{{ c / 1024 }}k</button>
      </div>
      <Skeleton v-if="!cat" kind="rows" :n="6" />
      <template v-else>
        <p class="faint small">{{ $t(`ai.source.${cat.source}`) }}</p>
        <div v-for="r in cat.rows" :key="r.model" class="mrow">
          <div class="grow">
            <span class="mono name">{{ r.model }}</span>
            <div class="small muted">
              <span class="num">{{ $t('ai.gb', { n: r.size_gb }) }}</span>, {{ $t('ai.need', { n: r.need_gb }) }}<template v-if="r.year">, {{ r.year }}</template>
              <template v-if="r.verdict === 'partial'">, {{ $t('ai.onGpu', { n: r.gpu_pct }) }}</template>
            </div>
          </div>
          <span class="pill" :class="tone(r.verdict)">{{ $t(`ai.verdict.${r.verdict}`) }}</span>
          <span v-if="isIn(r.model)" class="pill accent">{{ $t('ai.installed') }}</span>
          <button v-else-if="r.verdict !== 'no'" class="btn sm" @click="pull(r.model)"><Icon name="download" :size="14" /> {{ $t('ai.pull') }}</button>
        </div>
        <p v-if="!cat.rows.length" class="empty-state">{{ $t('ai.empty') }}</p>
      </template>
    </Panel>
  </div>
</template>

<style scoped>
.mrow { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-top: 1px solid var(--line); flex-wrap: wrap; }
.mrow:first-of-type { border-top: 0; }
.grow { flex: 1 1 140px; min-width: 0; }
.name { overflow-wrap: anywhere; }
.ctx { margin-bottom: 8px; }
</style>
