<script setup lang="ts">
import { burst, floatXp, setSoundOn, sfx, soundOn, vibrate } from '../utils/habitsFx'
import { isDoneOn, isoDay, isScheduled, midnight, perfectStreak, weekdayOf, type HabitChecks, type HabitFreq, type HabitRow } from '../utils/habits'

useHead({ title: 'Habits · Bastion' })
/**
 * Habits (native since 2026-10-27; was an iframe of its own app in CT 204). The server keeps habits + the days each
 * was done (/api/habits); every streak / perfect-day number is worked out here from the viewer's local day.
 * Ticks are optimistic and roll back with a toast; polling picks up changes from another device.
 */
const { t } = useI18n()
const { optimistic } = useToast()
const route = useRoute(), router = useRouter()

interface Data { habits: HabitRow[], checks: Record<string, string[]> }
const data = ref<Data | null>(null)
const error = ref('')
const now = ref(new Date())
let writes = 0 // don't let a poll that started before a write overwrite it
async function load() {
  now.value = new Date()
  if (writes) return
  try {
    const r = await $fetch<Data>('/api/habits')
    if (!writes) { data.value = r; error.value = '' }
  } catch (e: any) { error.value = e?.data?.statusMessage || e?.message || 'failed' }
}
usePoll(load, 60_000)

const habits = computed(() => data.value?.habits ?? [])
const ck = computed<HabitChecks>(() => Object.fromEntries(Object.entries(data.value?.checks ?? {}).map(([k, v]) => [k, new Set(v)])))
const today = computed(() => midnight(now.value))
const perfect = computed(() => perfectStreak(habits.value, ck.value, today.value))

const tab = usePageTab('today')
const tabs = computed(() => [{ key: 'today', label: t('habits.tabs.today') }, { key: 'habits', label: t('habits.tabs.habits') }])

// --- writes (optimistic) ---
async function write<T>(apply: () => void, undo: () => void, save: () => Promise<T>, what: string) {
  writes++
  try { return await optimistic(apply, undo, save, what) } finally { writes-- }
}
function setChecked(hid: string, day: string, done: boolean) {
  if (!data.value) return
  const cur = data.value.checks[hid] ?? []
  data.value = { ...data.value, checks: { ...data.value.checks, [hid]: done ? [...new Set([...cur, day])] : cur.filter(d => d !== day) } }
}
function check(hid: string, day: string, done: boolean) {
  return write(() => setChecked(hid, day, done), () => setChecked(hid, day, !done),
    () => $fetch('/api/habits/check', { method: 'POST', body: { habit: hid, day, done } }), t('habits.what.check'))
}

const celebrating = ref<{ n: number, done: number } | null>(null)
const sound = ref(true)
onMounted(() => { sound.value = soundOn() })
function toggleSound() { sound.value = !sound.value; setSoundOn(sound.value); if (sound.value) sfx('check') }

function tick(hid: string, row: HTMLElement | null) {
  const day = isoDay(today.value), wd = weekdayOf(today.value)
  const done = !isDoneOn(ck.value, hid, day)
  const due = habits.value.filter(h => isScheduled(h, wd))
  const n = due.filter(h => isDoneOn(ck.value, h.id, day) || h.id === hid).length
  const allDone = done && n === due.length
  check(hid, day, done)
  if (!done) return
  sfx('check', n)
  burst(row?.querySelector('.box'), 16, 70); vibrate(12); floatXp(row, t('habits.xp'))
  if (allDone) {
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches
    setTimeout(() => { if (isDoneOn(ck.value, hid, day)) celebrating.value = { n: perfect.value, done: n } }, reduced ? 0 : 700)
  }
}

function pastDay(day: string, el: HTMLElement) {
  const h = openHabit.value
  if (!h) return
  const done = !isDoneOn(ck.value, h.id, day)
  check(h.id, day, done)
  if (done) { burst(el, 10, 40); sfx('check') }
}

const uid = () => (globalThis.crypto?.randomUUID?.() ?? `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`)
const editing = ref<HabitRow | null>(null)
async function save(f: { id?: string, title: string, freq: HabitFreq, days: number[] }) {
  if (!data.value) return
  const prev = data.value
  const id = f.id ?? uid()
  const old = habits.value.find(h => h.id === id)
  const row: HabitRow = { id, title: f.title, freq: f.freq, days: f.days, created: old?.created ?? Date.now() }
  editing.value = null
  await write(
    () => { data.value = { ...prev, habits: old ? prev.habits.map(h => (h.id === id ? row : h)) : [...prev.habits, row] } },
    () => { data.value = prev },
    () => $fetch('/api/habits/save', { method: 'POST', body: { id, title: f.title, freq: f.freq, days: f.days } }),
    t('habits.what.habit'),
  )
}
async function remove(id: string) {
  if (!data.value) return
  const prev = data.value
  if (editing.value?.id === id) editing.value = null
  if (route.query.h === id) closeDetail()
  await write(
    () => { data.value = { habits: prev.habits.filter(h => h.id !== id), checks: Object.fromEntries(Object.entries(prev.checks).filter(([k]) => k !== id)) } },
    () => { data.value = prev },
    () => $fetch('/api/habits/remove', { method: 'POST', body: { id } }),
    t('habits.what.delete'),
  )
}

// --- detail lives in the URL (?h=<id>) so the phone's back button closes it ---
const openHabit = computed(() => (typeof route.query.h === 'string' ? habits.value.find(h => h.id === route.query.h) : undefined))
function openDetail(id: string) { router.push({ query: { ...route.query, s: 'habits', h: id } }); scrollTo(0, 0) }
function closeDetail() { if (window.history.state?.back) router.back(); else router.replace({ query: { ...route.query, h: undefined } }) }
function editFromDetail() {
  editing.value = openHabit.value ?? null
  router.replace({ query: { ...route.query, h: undefined } })
  scrollTo(0, 0)
}
watch(tab, () => { editing.value = null })
</script>

<template>
  <div class="hb">
    <PageTabs v-model="tab" :tabs="tabs" />
    <div class="body">
    <p v-if="error" class="errbox">{{ error }} <button class="lnk" @click="load">{{ t('habits.retry') }}</button></p>
    <Skeleton v-if="!data" kind="cards" :n="3" />
    <template v-else>
      <HabitsToday v-if="tab === 'today'" :habits="habits" :checks="ck" :now="now" :perfect="perfect" :sound="sound" @toggle="tick" @sound="toggleSound" />
      <HabitsDetail v-else-if="openHabit" :habit="openHabit" :checks="ck" :now="now" @back="closeDetail" @edit="editFromDetail" @day="pastDay" />
      <HabitsList v-else :habits="habits" :checks="ck" :now="now" :editing="editing" @save="save" @cancel="editing = null" @open="openDetail" @remove="remove" />
    </template>
    </div>
    <HabitsCelebrate v-if="celebrating" :n="celebrating.n" :done="celebrating.done" :habits="habits" :checks="ck" :today="today" @close="celebrating = null" />
  </div>
</template>

<style scoped>
.hb { max-width: 640px; margin: 0 auto; }
/* the gap lives below the tabs: a skin's PageTabs may add a hidden marker before its row (Material) */
.body { display: flex; flex-direction: column; gap: 14px; }
</style>
