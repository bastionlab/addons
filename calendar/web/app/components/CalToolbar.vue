<script setup lang="ts">
import type { CalView } from '../utils/calendar'
/** Today / previous / next + the period title, the view switcher and New event (two compact rows on a phone) */
const cal = useCal()
const { t } = useI18n()
const VIEWS: { v: CalView, key: string }[] = [{ v: 'month', key: 'M' }, { v: 'week', key: 'W' }, { v: 'day', key: 'D' }, { v: 'agenda', key: 'A' }]
// phone header: the view button and the More button each own a small menu (one open at a time)
const viewMenu = ref(false), moreMenu = ref(false)
watch(viewMenu, o => { if (o) moreMenu.value = false })
watch(moreMenu, o => { if (o) viewMenu.value = false })
</script>

<template>
  <header v-if="cal.narrow" class="ph">
    <button type="button" class="pt" :aria-label="t('calendar.goTo') + ': ' + cal.title" @click="cal.pick = true">
      <span class="pt-ttl" aria-live="polite">{{ cal.title }}<Icon name="chevron-down" :size="16" /></span>
      <span v-if="cal.subtitle" class="pt-sub">{{ cal.subtitle }}</span>
    </button>
    <span v-if="cal.ready" class="ld" :class="{ on: cal.busy }" aria-hidden="true" />
    <button v-if="!cal.onToday" type="button" class="pill accent tdy" @click="cal.today()">{{ t('calendar.today') }}</button>
    <CalMenu v-model="viewMenu">
      <template #trigger>
        <button type="button" class="btn vw" aria-haspopup="menu" :aria-expanded="viewMenu" :aria-label="t('calendar.views')" @click="viewMenu = !viewMenu">
          {{ t('calendar.view.' + cal.view) }}<Icon name="chevron-down" :size="16" />
        </button>
      </template>
      <button v-for="x in VIEWS" :key="x.v" type="button" role="menuitemradio" :aria-checked="cal.view === x.v" :class="{ on: cal.view === x.v }" @click="cal.setView(x.v)">
        {{ t('calendar.view.' + x.v) }}<span class="sp" /><Icon v-if="cal.view === x.v" name="check" :size="16" />
      </button>
    </CalMenu>
    <CalMenu v-model="moreMenu">
      <template #trigger>
        <button type="button" class="btn icon" aria-haspopup="menu" :aria-expanded="moreMenu" :aria-label="t('calendar.menu')" @click="moreMenu = !moreMenu"><Icon name="ellipsis" :size="18" /></button>
      </template>
      <button type="button" role="menuitem" @click="cal.sheet = true"><Icon name="list-checks" :size="16" />{{ t('calendar.calendars') }}</button>
      <button type="button" role="menuitem" @click="cal.pick = true"><Icon name="calendar" :size="16" />{{ t('calendar.goTo') }}</button>
      <button type="button" role="menuitem" @click="cal.today()"><Icon name="clock" :size="16" />{{ t('calendar.today') }}</button>
      <button type="button" role="menuitem" @click="cal.reload()"><Icon name="refresh-cw" :size="16" />{{ t('calendar.refresh') }}</button>
    </CalMenu>
  </header>
  <button v-if="cal.narrow" type="button" class="fab" :disabled="!cal.editor.canCreate" :aria-label="t('calendar.new')" @click="cal.editor.openNew()"><Icon name="plus" :size="22" /></button>
  <header v-else class="tb">
    <div class="nav">
      <button type="button" class="btn" @click="cal.today()">{{ t('calendar.today') }}<kbd class="kb">T</kbd></button>
      <button type="button" class="btn icon" :aria-label="t('calendar.prev')" @click="cal.step(-1)"><Icon name="chevron-left" :size="18" /></button>
      <button type="button" class="btn icon" :aria-label="t('calendar.next')" @click="cal.step(1)"><Icon name="chevron-right" :size="18" /></button>
    </div>
    <div class="tt">
      <h1 class="ttl" aria-live="polite">{{ cal.title }}</h1>
      <span v-if="cal.ready" class="ld" :class="{ on: cal.busy }" aria-hidden="true" />
    </div>
    <div class="seg views" role="group" :aria-label="t('calendar.views')">
      <button v-for="x in VIEWS" :key="x.v" type="button" :class="{ on: cal.view === x.v }" :aria-pressed="cal.view === x.v" @click="cal.setView(x.v)">{{ t('calendar.view.' + x.v) }}<kbd class="kb">{{ x.key }}</kbd></button>
    </div>
    <div class="acts">
      <button v-if="!cal.wide" type="button" class="btn icon" :aria-label="t('calendar.calendars')" @click="cal.sheet = true"><Icon name="list-checks" :size="18" /></button>
      <button type="button" class="btn primary newb" :disabled="!cal.editor.canCreate" :aria-label="t('calendar.new')" @click="cal.editor.openNew()">
        <Icon name="plus" :size="16" /><span class="nl">{{ t('calendar.new') }}</span><kbd class="kb">N</kbd>
      </button>
    </div>
  </header>
</template>

<style scoped>
.tb { display: grid; grid-template-columns: auto minmax(0, 1fr) auto auto; align-items: center; gap: 8px 14px; }
.nav, .acts { display: flex; align-items: center; gap: 6px; }
.tt { display: flex; align-items: center; gap: 8px; min-width: 0; }
.ld { flex: none; width: 6px; height: 6px; border-radius: 50%; background: var(--accent); opacity: 0; transition: opacity .2s .25s; }
.ld.on { opacity: .8; animation: ld 1s ease-in-out infinite alternate; }
@keyframes ld { from { opacity: .25; } to { opacity: .9; } }
@media (prefers-reduced-motion: reduce) { .ld.on { animation: none; } }
.ttl { margin: 0; font-size: 20px; font-weight: 600; letter-spacing: -.01em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.views > button { height: 32px; padding: 0 12px; display: inline-flex; align-items: center; }
.newb { height: 34px; padding: 0 14px; }

/* the key hints: only where there is a keyboard and a precise pointer */
.kb { display: none; }
@media (hover: hover) and (pointer: fine) {
  .kb { display: inline-block; margin-left: 7px; padding: 2px 5px; border: 1px solid var(--line-2); border-radius: 4px; font: 600 10px/1 var(--mono); color: var(--faint); }
  .views > button.on .kb { color: inherit; border-color: color-mix(in srgb, currentColor 35%, transparent); }
  .newb .kb { color: inherit; border-color: color-mix(in srgb, currentColor 40%, transparent); opacity: .75; }
}

/* phone: one compact row; the + is a round button above the tab bar, left of the assistant's mic (48 px + 12 px gaps) */
.ph { display: flex; align-items: center; gap: 8px; min-height: 44px; }
.pt { flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: flex-start; gap: 1px; min-height: 44px; justify-content: center; padding: 0; border: 0; background: none; color: var(--text); font: inherit; text-align: left; cursor: pointer; }
.pt-ttl { display: inline-flex; align-items: center; gap: 4px; max-width: 100%; font-size: 18px; font-weight: 600; letter-spacing: -.01em; line-height: 1.2; white-space: nowrap; }
.pt-ttl svg { flex: none; color: var(--muted); }
.pt-sub { font-size: 12px; color: var(--muted); line-height: 1.2; }
.tdy { flex: none; min-height: 36px; padding: 0 12px; font: inherit; font-size: 13px; font-weight: 500; cursor: pointer; }
.ph .btn { min-height: 40px; }
.ph .btn.icon { width: 40px; height: 40px; padding: 0; }
.vw { gap: 4px; padding: 0 10px 0 12px; }
.fab {
  position: fixed; z-index: 40; right: calc(12px + 48px + 12px); bottom: calc(var(--tabbar) + 12px);
  width: 48px; height: 48px; border-radius: 50%; display: grid; place-items: center; padding: 0; cursor: pointer;
  border: 0; background: var(--accent); color: var(--bg); box-shadow: 0 4px 14px rgb(0 0 0 / .35); -webkit-tap-highlight-color: transparent;
  transition: transform .12s;
}
.fab:active { transform: scale(.94); }
.fab:disabled { opacity: .45; }
@media (min-width: 641px) and (max-width: 899px) { .tb { grid-template-columns: auto minmax(0, 1fr) auto auto; } }
</style>
