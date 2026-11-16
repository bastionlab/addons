<script setup lang="ts">
/**
 * Home card of the Daily briefing add-on (addon.yaml home: true). It fills the tile Home gives it (HomeItem provides
 * `homeBox` / `homeSize`): one column = icon + name, a short wide tile = the summary (2 lines) and a muted count
 * line, 2 rows = header, summary and count line, 3+ rows = the sections as rows too. The whole card opens /briefing.
 */
const { t } = useI18n()
const box = inject<ComputedRef<{ w: number, h: number }>>('homeBox', computed(() => ({ w: 2, h: 1 })))
const size = inject<ComputedRef<'s' | 'm' | 'l'>>('homeSize', computed(() => 'm'))
const { data, error, refresh } = useFetch<any>('/api/briefing', { server: false, lazy: true })
let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => { timer = setInterval(() => refresh(), 5 * 60_000) })
onUnmounted(() => clearInterval(timer))

const row = computed(() => data.value?.today ?? null)
const sections = computed(() => (row.value ? briefingSections(row.value.facts, row.value.matters, t) : []))
const urgent = computed(() => sections.value.filter(s => s.matters))
const unread = computed(() => (row.value ? briefingUnreadable(row.value.facts, t) : ''))
const quiet = computed(() => !!row.value && !urgent.value.length)
const weather = computed(() => sections.value.find(s => s.id === 'weather'))
// what the card says first: the model's sentences, or on a quiet day one muted line (never "all clear" when something could not be read)
const headline = computed(() => {
  if (error.value) return t('briefing.home.error')
  if (!data.value) return ''
  if (!row.value) return data.value.running || data.value.nextAt <= Date.now() ? t('briefing.home.writing') : t('briefing.home.next', { time: data.value.time })
  if (quiet.value) return unread.value || t('briefing.quiet')
  return row.value.summary
})
const countLine = computed(() => {
  if (!row.value) return ''
  if (quiet.value) return weather.value?.lines[0] ?? ''
  return [...urgent.value.map(s => s.short), ...(unread.value ? [unread.value] : [])].join(' · ')
})
// rows by urgency: alerts, then the calendar, then whatever else needs a look, then the rest; the list shows only whole rows that fit
const ranked = computed(() => {
  const rank = (s: { id: string, matters: boolean }) => (s.id === 'system' && s.matters ? 0 : s.id === 'calendar' && s.matters ? 1 : s.matters ? 2 : 3)
  return [...sections.value].sort((a, b) => rank(a) - rank(b))
})
const tall = computed(() => box.value.h >= 2 && size.value === 'l')
const showRows = computed(() => tall.value && box.value.h >= 3 && sections.value.length > 0)
const warn = computed(() => !!unread.value || urgent.value.some(s => s.tone))
</script>

<template>
  <NuxtLink to="/briefing" class="hb press" :class="[size, { tall }]" :aria-label="t('briefing.title')">
    <span class="ti"><Icon name="alarm-clock" :size="18" /></span>
    <span class="body">
      <span class="name">{{ t('briefing.home.name') }}</span>
      <Skeleton v-if="!data && !error" kind="lines" :n="2" class="sk" />
      <template v-else>
        <span class="head" :class="{ muted: quiet || !row }">{{ headline }}</span>
        <span v-if="countLine" class="count">{{ countLine }}</span>
        <span v-if="showRows" class="rows">
          <span v-for="s in ranked" :key="s.id" class="r" :class="{ dim: !s.matters }">
            <Icon :name="s.icon" :size="14" class="faint" />
            <span class="rn">{{ s.title }}</span>
            <span class="rv" :class="s.tone">{{ s.lines[0] }}</span>
          </span>
        </span>
      </template>
    </span>
    <span v-if="warn" class="dot warn st" />
  </NuxtLink>
</template>

<style scoped>
.hb {
  position: relative; display: flex; align-items: flex-start; gap: 10px; min-width: 0; height: 100%; padding: 6px 12px; overflow: hidden;
  border-radius: var(--radius); color: var(--text); background: var(--panel); border: 1px solid var(--line);
  transition: border-color var(--dur) var(--ease-out), background var(--dur) var(--ease-out), transform var(--dur-fast) var(--ease-out);
}
.hb:hover { text-decoration: none; border-color: var(--line-2); background: var(--panel-2); }
.ti { display: grid; place-items: center; flex: none; width: 30px; height: 30px; border-radius: var(--radius-sm); background: var(--panel-2); color: var(--muted); }
.hb:hover .ti { color: var(--accent); }
.body { display: flex; flex-direction: column; gap: 1px; min-width: 0; min-height: 0; flex: 1; align-self: stretch; }
.name { font-weight: 600; font-size: 12px; color: var(--muted); line-height: 1.2; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.head { font-size: 13px; line-height: 1.25; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow-wrap: anywhere; }
.count { font-size: 11.5px; line-height: 1.3; color: var(--faint); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sk { margin-top: 2px; }
.rows { display: flex; flex-flow: column wrap; align-content: flex-start; flex: 1 1 0; gap: 0 8px; margin-top: 8px; padding-top: 6px; border-top: 1px solid var(--line); min-height: 0; overflow: hidden; }
/* a row that does not fit wraps into a second column outside the clip, so only whole rows show */
.r { width: 100%; flex: none; height: 26px; box-sizing: border-box; display: flex; align-items: center; gap: 8px; min-width: 0; font-size: 13px; padding: 2px 0; }
.r.dim { color: var(--muted); }
.rn { flex: none; width: 76px; color: var(--muted); font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rv { min-width: 0; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rv.warn { color: var(--warn); }
.rv.bad { color: var(--bad); }
/* a short wide tile (2 x 1) has no room for the name: the icon says what it is */
.hb:not(.tall):not(.s) .name { display: none; }
.hb:not(.tall):not(.s) .ti { align-self: center; }
/* a tall tile has room: a real header and a 3-line summary */
.tall { display: grid; grid-template-columns: auto minmax(0, 1fr); grid-template-rows: auto auto auto minmax(0, 1fr); align-items: center; gap: 6px 10px; padding: 12px 14px; }
.tall .body { display: contents; }
.tall .head, .tall .count, .tall .rows, .tall .sk { grid-column: 1 / -1; }
.tall .rows { align-self: stretch; margin-top: 2px; }
.tall .name { font-size: 14px; color: var(--text); padding-right: 12px; }
.tall .head { -webkit-line-clamp: 3; line-clamp: 3; font-size: 14px; }
/* the warning dot, at every size */
.st { position: absolute; top: 8px; right: 8px; width: 7px; height: 7px; box-shadow: none; }
/* one column: icon over name, a dot when something needs a look */
.s { flex-direction: column; align-items: center; justify-content: center; gap: 6px; padding: 8px 6px; text-align: center; }
.s .body { flex: none; align-items: center; max-width: 100%; }
.s .head, .s .count, .s .rows, .s .sk { display: none; }
@media (max-width: 640px) { .ti { width: 28px; height: 28px; } }
</style>
