<script setup lang="ts">
/**
 * Home card of the Widgets add-on (addon.yaml home: true). It fills the tile Home gives it: a small tile shows a
 * summary (name + how many widgets), a tile 2+ rows tall shows the widgets themselves as a scrolling grid.
 * Home's edit mode puts class `editing` on the tile around this card (HomeItem); that is the signal for "Edit".
 */
const { t } = useI18n()
const api = useWidgets()
const root = ref<HTMLElement>()
const editing = ref(false)
const sheet = ref(false)
const packs = ref<string[]>([])
const box = inject<ComputedRef<{ w: number, h: number }>>('homeBox', computed(() => ({ w: 2, h: 1 })))
const tall = computed(() => box.value.h >= 2)
const count = computed(() => api.onHome.value.length)
const sub = computed(() => (count.value ? t('widgets.count', { n: count.value }) : t(editing.value ? 'widgets.emptyEdit' : 'widgets.empty')))
let mo: MutationObserver | undefined
onMounted(() => {
  const tile = root.value?.closest('.it')
  if (tile) {
    const sync = () => { editing.value = tile.classList.contains('editing'); if (!editing.value) sheet.value = false }
    sync()
    mo = new MutationObserver(sync)
    mo.observe(tile, { attributes: true, attributeFilter: ['class'] })
  }
  $fetch<{ packs: { pack: string }[] }>('/api/widgets/library').then(r => (packs.value = r.packs.map(p => p.pack))).catch(() => {})
})
onUnmounted(() => mo?.disconnect())
</script>

<template>
  <div ref="root" class="hw">
    <div class="hd">
      <span class="ti"><Icon name="grid" :size="18" /></span>
      <span class="txt">
        <span class="name">{{ t('widgets.title') }}</span>
        <span class="line">{{ sub }}</span>
      </span>
      <button v-if="editing" type="button" class="btn sm ed" @click="sheet = true"><Icon name="edit" :size="16" /> {{ t('widgets.edit') }}</button>
    </div>
    <div v-if="tall && count" class="gr">
      <div v-for="w in api.onHome.value" :key="w.id" class="c" :class="`sz-${w.size}`">
        <WidgetView :def="w" :packs="packs" />
      </div>
    </div>
    <WidgetsBuilder v-if="sheet" :api="api" :packs="packs" @close="sheet = false" />
  </div>
</template>

<style scoped>
.hw { display: flex; flex-direction: column; gap: 8px; padding: 10px 12px; background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); overflow: hidden; }
.hd { display: flex; align-items: center; gap: 10px; min-width: 0; }
.ti { display: grid; place-items: center; width: 32px; height: 32px; flex: none; border-radius: var(--radius-sm); background: var(--accent-soft); color: var(--accent); }
.txt { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.name { font-weight: 600; }
.line { color: var(--muted); font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.gr { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); grid-auto-rows: 104px; gap: 8px; overflow-y: auto; min-height: 0; }
.c { min-width: 0; min-height: 0; }
.sz-S { grid-column: span 1; }
.sz-M { grid-column: span 2; }
.sz-L { grid-column: span 2; grid-row: span 2; }
@media (min-width: 900px) { .gr { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
/* HomeItem makes the card inert while editing; the one control that must work stays clickable */
.ed { flex: none; pointer-events: auto; }
@media (pointer: coarse) { .ed { min-height: 36px; } }
</style>
