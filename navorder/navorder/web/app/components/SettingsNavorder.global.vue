<script setup lang="ts">
/** Settings → Add-ons → Sidebar order: drag the pages into the order this kind of device shows them. */
const { ordered, set, reset, kind, custom } = useNavOrder<{ to: string, icon: string, label: string }>()
const drag = ref('')
const list = ref<{ to: string, icon: string, label: string }[]>([])
watch(ordered, v => { if (!drag.value) list.value = [...v] }, { immediate: true })

const rows = ref<HTMLElement[]>([])
function down(e: PointerEvent, to: string) {
  drag.value = to
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
}
function move(e: PointerEvent) {
  if (!drag.value) return
  const els = rows.value.filter(Boolean)
  // the row whose vertical middle the finger has passed decides the new slot
  let target = els.findIndex(el => e.clientY < el.getBoundingClientRect().top + el.offsetHeight / 2)
  if (target < 0) target = els.length - 1
  const from = list.value.findIndex(n => n.to === drag.value)
  if (from < 0 || from === target) return
  const next = [...list.value]
  next.splice(target, 0, next.splice(from, 1)[0]!)
  list.value = next
}
function up() {
  if (!drag.value) return
  drag.value = ''
  set(list.value.map(n => n.to))
}
</script>

<template>
  <div class="no">
    <p class="small faint">Drag a page by its handle. This order is for your {{ kind }} and applies to the sidebar and the phone menu.</p>
    <div class="rows">
      <div v-for="n in list" :key="n.to" :ref="el => { const i = list.indexOf(n); if (el) rows[i] = el as HTMLElement }" class="row" :class="{ lift: drag === n.to }">
        <span class="grip" aria-label="Drag to reorder" @pointerdown.prevent="down($event, n.to)" @pointermove="move" @pointerup="up" @pointercancel="up">
          <i /><i /><i />
        </span>
        <Icon :name="n.icon" :size="18" class="faint" />
        <span class="name">{{ n.label }}</span>
      </div>
    </div>
    <button v-if="custom" type="button" class="reset" @click="reset">Reset to default</button>
  </div>
</template>

<style scoped>
.no { display: flex; flex-direction: column; gap: 10px; }
.rows { display: flex; flex-direction: column; gap: 4px; }
.row { display: flex; align-items: center; gap: 10px; padding: 4px 10px 4px 4px; border: 1px solid var(--line); border-radius: var(--radius-sm); background: var(--panel); }
.row.lift { background: var(--panel-2); border-color: var(--accent); }
.grip { display: flex; flex-direction: column; justify-content: center; gap: 3px; width: 44px; height: 40px; padding: 0 14px; cursor: grab; touch-action: none; user-select: none; }
.grip i { display: block; height: 2px; border-radius: 1px; background: var(--muted); }
.name { flex: 1; min-width: 0; }
.reset { align-self: flex-start; }
</style>
