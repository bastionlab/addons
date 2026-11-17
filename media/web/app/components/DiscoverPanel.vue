<script setup lang="ts">
/**
 * Suggestions in three rows (watch history, trending, all-time). Titles the library has or once had are filtered
 * out by the agent. Request goes through the allowlisted media_request action (Seerr then hands it to Radarr/Sonarr);
 * the card flips to Requested at once and rolls back if the action fails.
 */
const { t } = useI18n()
const { run } = useActions()

// "Load more" raises depth: the agent then reads deeper TMDB pages; the rows already on screen stay until the new data lands
const depth = ref(1)
const { data, pending, error } = useFetch<{ sections: any[], maxDepth?: number }>('/api/media/discover', { lazy: true, server: false, query: { depth } })
const canMore = computed(() => depth.value < (data.value?.maxDepth ?? 5))

// 'kind:tmdbId' of cards flipped to Requested
const hiddenSeen = reactive<Record<string, true>>({})
const shown = (items: any[]) => items.filter(i => !hiddenSeen[key(i)])
const { optimistic } = useToast()

function seen(i: any) {
  const k = key(i)
  return optimistic(
    () => { hiddenSeen[k] = true },
    () => { delete hiddenSeen[k] },
    () => $fetch('/api/media/discover/seen', { method: 'POST', body: { kind: i.kind, tmdbId: i.tmdbId } }),
    t('media.discover.seenWhat'),
  )
}

function dismiss(i: any) {
  const k = key(i)
  return optimistic(
    () => { hiddenSeen[k] = true },
    () => { delete hiddenSeen[k] },
    () => $fetch('/api/media/discover/seen', { method: 'POST', body: { kind: i.kind, tmdbId: i.tmdbId, dismiss: true } }),
    t('media.discover.dismissWhat'),
  )
}

const requested = reactive<Record<string, true>>({})
const key = (i: any) => `${i.kind}:${i.tmdbId}`

// series: Request opens a season picker first (like Seerr); a film is requested right away
const picking = ref('')
const seasons = ref<{ n: number, episodes: number, known: boolean }[]>([])
const chosen = ref<number[]>([])
const loadingSeasons = ref(false)

async function open(i: any) {
  if (i.kind !== 'series') return request(i)
  if (picking.value === key(i)) { picking.value = ''; return }
  picking.value = key(i)
  seasons.value = []
  chosen.value = []
  loadingSeasons.value = true
  try {
    seasons.value = (await $fetch<any>('/api/media/discover/seasons', { query: { tmdbId: i.tmdbId } })).seasons ?? []
  } catch { seasons.value = [] }
  loadingSeasons.value = false
}
const toggle = (n: number) => { chosen.value = chosen.value.includes(n) ? chosen.value.filter(x => x !== n) : [...chosen.value, n] }

async function request(i: any, picked: number[] = []) {
  const k = key(i)
  if (requested[k]) return
  requested[k] = true // optimistic; the jobs tray reports a failure and the card goes back to Request
  picking.value = ''
  const job = await run('media_request', { kind: i.kind, tmdbId: i.tmdbId, ...(picked.length ? { seasons: picked } : {}) })
  if (job.state !== 'done') delete requested[k]
}
</script>

<template>
  <div class="disc">
    <Skeleton v-if="pending && !data" kind="cards" :n="3" />
    <div v-else-if="error && !data" class="errbox">{{ t('media.discover.error', { msg: error.statusMessage || error.message }) }}</div>
    <template v-else>
      <Panel v-for="s in data?.sections ?? []" :id="`disc-${s.key}`" :key="s.key" :title="s.title">
        <div v-if="!s.items.length" class="small muted">{{ t('media.discover.empty') }}</div>
        <div v-else class="row scroll-x">
          <article v-for="i in shown(s.items)" :key="key(i)" class="card">
            <img :src="i.poster" :alt="t('media.discover.poster', { title: i.title })" loading="lazy" decoding="async" width="342" height="513">
            <div class="meta">
              <b class="ttl">{{ i.title }}</b>
              <div class="small muted">
                {{ i.year || '' }}
                <span class="pill">{{ t(i.kind === 'series' ? 'media.discover.series' : 'media.discover.film') }}</span>
                <span v-if="i.rating" class="pill accent num">{{ i.rating }}</span>
              </div>
              <div v-if="i.because" class="small faint">{{ t('media.discover.because', { title: i.because }) }}</div>
              <p class="small muted ov">{{ i.overview }}</p>
            </div>
            <span v-if="requested[key(i)]" class="pill ok done">{{ t('media.discover.requested') }}</span>
            <div v-else-if="picking === key(i)" class="pick">
              <Skeleton v-if="loadingSeasons" kind="lines" :n="2" />
              <template v-else>
                <div class="chips">
                  <button v-for="se in seasons" :key="se.n" class="chip" :class="{ on: chosen.includes(se.n) }" :title="`${se.episodes} ep`" @click="toggle(se.n)">{{ t('media.discover.season', { n: se.n }) }}</button>
                </div>
                <div class="acts">
                  <button class="btn primary sm" @click="request(i, chosen)" :disabled="!chosen.length">{{ t('media.discover.requestN', { n: chosen.length }) }}</button>
                  <button class="btn sm" @click="request(i)">{{ t('media.discover.all') }}</button>
                </div>
              </template>
            </div>
            <div v-else class="acts">
              <button class="btn primary sm" @click="open(i)">{{ t('media.discover.request') }}</button>
            </div>
            <div v-if="!requested[key(i)] && picking !== key(i)" class="acts">
              <button class="btn ghost sm" @click="seen(i)">{{ t('media.discover.seen') }}</button>
              <button class="btn ghost sm" @click="dismiss(i)">{{ t('media.discover.dismiss') }}</button>
            </div>
          </article>
        </div>
      </Panel>
      <div v-if="canMore" class="more">
        <button class="btn" :disabled="pending" @click="depth++">{{ t(pending ? 'media.discover.loadingMore' : 'media.discover.more') }}</button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.disc { display: flex; flex-direction: column; gap: 16px; }
.row { display: flex; gap: 12px; padding-bottom: 6px; scroll-snap-type: x proximity; }
.card { flex: none; width: 200px; display: flex; flex-direction: column; gap: 8px; scroll-snap-align: start; }
.card img { width: 100%; aspect-ratio: 2 / 3; object-fit: cover; border-radius: var(--radius-sm); background: var(--panel-2); border: 1px solid var(--line); }
.meta { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
.ttl { font-size: 13px; line-height: 1.25; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.ov { margin: 0; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.pick { display: flex; flex-direction: column; gap: 6px; }
.chips { display: flex; flex-wrap: wrap; gap: 4px; }
.acts { display: flex; gap: 6px; }
.acts .btn { flex: 1; }
.more { display: flex; justify-content: center; }
.done { align-self: flex-start; }
@media (pointer: coarse) { .card .btn { min-height: 36px; } }
@media (max-width: 640px) { .card { width: 176px; } }
</style>
