<script setup lang="ts">
/**
 * Home card of the Alert watch add-on (addon.yaml home: true). It fills the tile Home gives it (HomeItem provides
 * `homeBox` / `homeSize`): one column = icon + status dot, a short wide tile = status dot, one line and the time,
 * 2+ rows add the buttons. The header opens /alerts; Execute fix goes through sessionStorage (alertwatchExecute).
 */
const { t } = useI18n()
const box = inject<ComputedRef<{ w: number, h: number }>>('homeBox', computed(() => ({ w: 2, h: 1 })))
const size = inject<ComputedRef<'s' | 'm' | 'l'>>('homeSize', computed(() => 'm'))
const { data, error, refresh } = useFetch<any>('/api/alertwatch', { server: false, lazy: true })
let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => { timer = setInterval(() => refresh(), 60_000) })
onUnmounted(() => clearInterval(timer))

const item = computed(() => data.value?.open?.[0] ?? null)
const run = computed(() => item.value?.run ?? null)
const investigating = computed(() => !!item.value && !run.value?.done)
const tone = computed(() => (!item.value ? 'ok' : investigating.value ? 'warn' : 'bad'))
const line = computed(() => {
  if (error.value && !data.value) return t('alertwatch.error')
  if (!data.value) return ''
  if (!item.value) return data.value.quietSince ? t('alertwatch.quietSince', { time: fmtDate(data.value.quietSince, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) }) : t('alertwatch.quietNow')
  if (investigating.value) return alertPlain(item.value.msg)
  return run.value.cause || alertPlain(item.value.msg)
})
const sub = computed(() => (item.value ? (investigating.value ? t('alertwatch.investigating') : ago(item.value.at)) : ''))
const canExec = computed(() => !!run.value?.done && !run.value.allok && !run.value.executed && !!data.value?.chat)
const tall = computed(() => box.value.h >= 2 && size.value === 'l')
</script>

<template>
  <div class="ha" :class="[size, { tall }]">
    <NuxtLink to="/alerts" class="hd press" :aria-label="t('alertwatch.title')">
      <span class="ti"><Icon name="siren" :size="18" /></span>
      <span class="name">{{ t('alertwatch.home.name') }}</span>
      <span v-if="data" class="dot st" :class="tone" />
    </NuxtLink>
    <Skeleton v-if="!data && !error" kind="lines" :n="2" class="sk" />
    <div v-else class="bd">
      <span class="head" :class="{ muted: !item }">{{ line }}</span>
      <span v-if="sub" class="count">{{ sub }}</span>
      <span v-if="item && data.chat" class="acts">
        <NuxtLink :to="'/chat?c=' + data.chat" class="btn sm">{{ t('alertwatch.openChat') }}</NuxtLink>
        <button v-if="canExec" type="button" class="btn sm primary" @click="alertwatchExecute(data.chat, run.turn)">{{ t('alertwatch.execute') }}</button>
      </span>
    </div>
  </div>
</template>

<style scoped>
.ha {
  position: relative; display: flex; flex-direction: column; gap: 4px; min-width: 0; height: 100%; padding: 6px 12px; overflow: hidden;
  border-radius: var(--radius); color: var(--text); background: var(--panel); border: 1px solid var(--line);
}
.hd { display: flex; align-items: center; gap: 8px; min-width: 0; color: var(--text); }
.hd:hover { text-decoration: none; }
.ti { display: grid; place-items: center; flex: none; width: 30px; height: 30px; border-radius: var(--radius-sm); background: var(--panel-2); color: var(--muted); }
.hd:hover .ti { color: var(--accent); }
.name { flex: 1; min-width: 0; font-weight: 600; font-size: 12px; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.st { flex: none; width: 8px; height: 8px; box-shadow: none; }
.bd { display: flex; flex-direction: column; gap: 2px; min-width: 0; min-height: 0; }
.head { font-size: 13px; line-height: 1.25; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.count { font-size: 11.5px; line-height: 1.3; color: var(--faint); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.acts { display: none; gap: 6px; flex-wrap: wrap; margin-top: 4px; }
.sk { margin-top: 2px; }
/* a short wide tile (2 x 1): icon and one line side by side, no header text */
.ha:not(.tall):not(.s) { flex-direction: row; align-items: center; gap: 10px; }
.ha:not(.tall):not(.s) .name { display: none; }
.ha:not(.tall):not(.s) .st { position: absolute; top: 8px; right: 8px; }
.ha:not(.tall):not(.s) .bd { flex: 1; }
/* a tall tile has room for the text and buttons */
.tall { padding: 12px 14px; gap: 8px; }
.tall .name { font-size: 14px; color: var(--text); }
.tall .head { white-space: normal; display: -webkit-box; -webkit-line-clamp: 3; line-clamp: 3; -webkit-box-orient: vertical; overflow-wrap: anywhere; font-size: 14px; }
.tall .acts { display: flex; }
/* one column: icon over a dot */
.s { align-items: center; justify-content: center; padding: 8px 6px; }
.s .bd, .s .sk, .s .name { display: none; }
.s .hd { flex-direction: column; gap: 6px; }
@media (max-width: 640px) { .ti { width: 28px; height: 28px; } }
@media (pointer: coarse) { .acts .btn { min-height: 32px; } }
</style>
