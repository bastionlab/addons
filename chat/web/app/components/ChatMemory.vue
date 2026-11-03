<script setup lang="ts">
// the chat memory: what Claude and the local model are told about the owner and the server in every chat
const emit = defineEmits<{ close: [] }>()
const { t: tr } = useI18n()
const { facts, count, load, add, edit, pin, del } = useMemory()
const err = ref('')
const draft = ref('')
const editing = ref<number | null>(null)
const text = ref('')
onMounted(load)

const run = async (p: Promise<any>) => { err.value = ''; try { await p } catch (e: any) { err.value = e?.data?.statusMessage || e?.message || 'failed' } }
const addNew = () => { const t = draft.value.trim(); if (t) run(add(t).then(() => (draft.value = ''))) }
const startEdit = (f: { id: number, text: string }) => { editing.value = f.id; text.value = f.text }
const saveEdit = () => { const id = editing.value; if (id == null) return; editing.value = null; if (text.value.trim()) run(edit(id, text.value)) }
</script>

<template>
  <div class="sheet">
    <div class="sh"><b><Icon name="brain" :size="18"/> {{ $t('memory.title') }}</b><span class="faint small">{{ count }}</span>
      <button type="button" class="btn ghost" @click="emit('close')">{{ $t('memory.close') }}</button></div>
    <div class="muted small">{{ $t('memory.hint') }}</div>
    <form class="row" @submit.prevent="addNew">
      <input v-model="draft" class="grow" maxlength="300" :placeholder="$t('memory.add')">
      <button type="submit" class="btn" :disabled="!draft.trim()">{{ $t('memory.addBtn') }}</button>
    </form>
    <div v-if="err" class="bad small">{{ err }}</div>
    <div v-if="!facts.length" class="muted small empty">{{ $t('memory.empty') }}</div>
    <div v-for="f in facts" :key="f.id" class="fact" :class="{ pinned: f.pinned }">
      <form v-if="editing === f.id" class="row" @submit.prevent="saveEdit">
        <input v-model="text" class="grow" maxlength="300" autofocus>
        <button type="submit" class="btn">{{ $t('common.save') }}</button>
        <button type="button" class="btn ghost" @click="editing = null">{{ $t('common.cancel') }}</button>
      </form>
      <template v-else>
        <span class="ft" @click="startEdit(f)">{{ f.text }}</span>
        <span class="fa">
          <button type="button" class="btn ghost" :title="f.pinned ? $t('memory.unpin') : $t('memory.pin')" @click="run(pin(f.id, !f.pinned))"><Icon name="pin" :size="16"/></button>
          <button type="button" class="btn ghost" :title="$t('memory.edit')" @click="startEdit(f)" :aria-label="$t('memory.edit')"><Icon name="pencil" :size="16"/></button>
          <button type="button" class="btn ghost" :title="$t('memory.delete')" @click="run(del(f.id))" :aria-label="$t('memory.delete')"><Icon name="trash-2" :size="16"/></button>
        </span>
      </template>
    </div>
  </div>
</template>

<style scoped>
.sheet { display: flex; flex-direction: column; gap: 10px; }
.sh { display: flex; align-items: center; gap: 8px; }
.sh b { flex: 1; }
.row { display: flex; align-items: center; gap: 8px; }
.grow { flex: 1; min-width: 0; }
.fact { display: flex; align-items: center; gap: 8px; border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 8px 10px; }
.fact.pinned { border-left: 3px solid var(--accent); }
.ft { flex: 1; min-width: 0; overflow-wrap: anywhere; cursor: text; }
.fa { display: flex; flex-shrink: 0; }
.bad { color: var(--bad); }
.empty { padding: 8px 0; }
@media (pointer: coarse) { .fa .btn { min-width: 40px; min-height: 40px; } }
</style>
