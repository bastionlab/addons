<script setup lang="ts">
useHead({ title: 'Calendar · Bastion' })
/**
 * Calendar: Google is the source of truth (/api/gcal/* -> agent gcal.py), nothing is cached here beyond the visible range.
 * This page is the shell; state lives in useCalendar / useCalEditor, the pieces in components/Cal*.vue.
 * Not here: drag-to-move, a home widget, attendees, other reminder settings.
 */
const { t } = useI18n()
const cal = useCalendar()
provide('cal', cal)

const issues = computed(() => [
  ...(cal.error ? [cal.error] : []),
  ...cal.errors.map(e => `${e.account}${e.calendar ? ' / ' + e.calendar : ''}: ${e.error}`),
].map(s => s.slice(0, 240)))

// phone: swipe sideways = previous / next (vertical scrolls and sideways-scrolling grids are left alone)
let sx = 0, sy = 0, swipe = false
function down(e: TouchEvent) {
  const el = e.target as HTMLElement
  const scroller = el.closest<HTMLElement>('.gs')
  swipe = e.touches.length === 1 && !(scroller && scroller.scrollWidth > scroller.clientWidth + 2) && !el.closest('input, select, textarea')
  sx = e.touches[0]?.clientX ?? 0; sy = e.touches[0]?.clientY ?? 0
}
function up(e: TouchEvent) {
  if (!swipe) return
  swipe = false
  const dx = (e.changedTouches[0]?.clientX ?? 0) - sx, dy = (e.changedTouches[0]?.clientY ?? 0) - sy
  if (Math.abs(dx) > 60 && Math.abs(dx) > 1.6 * Math.abs(dy)) cal.step(dx < 0 ? 1 : -1)
}
</script>

<template>
  <div class="cal">
    <CalToolbar />
    <div class="body">
      <aside v-if="cal.wide" class="side"><CalSidebar /></aside>
      <section class="main" @touchstart.passive="down" @touchend.passive="up">
        <div v-if="issues.length" class="errbox strip" role="status">
          <div v-for="s in issues" :key="s">{{ s }}</div>
        </div>
        <div v-if="cal.noAccount" class="empty-state connect">
          <Icon name="calendar" :size="28" />
          <p>{{ t('calendar.connect.text') }}</p>
          <NuxtLink to="/settings?s=connections" class="btn primary">{{ t('calendar.connect.btn') }}</NuxtLink>
        </div>
        <div v-else-if="!cal.ready" class="skel">
          <Skeleton v-for="i in (cal.view === 'agenda' ? 0 : cal.view === 'day' ? 2 : 5)" :key="i" kind="band" :n="cal.view === 'day' ? 1 : 7" />
          <Skeleton v-if="cal.view === 'agenda'" kind="rows" :n="6" />
        </div>
        <CalMonth v-else-if="cal.view === 'month'" />
        <CalAgenda v-else-if="cal.view === 'agenda'" />
        <CalGrid v-else :key="cal.view" />
      </section>
    </div>

    <CalEditor />
    <CalSheet v-if="!cal.wide" :open="cal.sheet" :label="t('calendar.calendars')" @esc="cal.sheet = false" @backdrop="cal.sheet = false">
      <CalSidebar />
      <template #footer>
        <div class="sheet-foot"><button type="button" class="btn" @click="cal.sheet = false">{{ t('calendar.close') }}</button></div>
      </template>
    </CalSheet>
  </div>
</template>

<style scoped>
/* a fixed-height workspace: the grid scrolls inside it, the page itself does not */
.cal { display: flex; flex-direction: column; gap: 14px; height: calc(100dvh - 56px); min-height: 520px; margin-bottom: -32px; min-width: 0; }
.body { flex: 1; min-height: 0; display: flex; gap: 18px; }
.side { width: 236px; flex: none; overflow-y: auto; padding: 2px 2px 12px 0; }
.main { position: relative; flex: 1; min-width: 0; display: flex; flex-direction: column; background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); overflow: hidden; }
.strip { border-radius: 0; border-width: 0 0 1px; font-size: 12.5px; padding: 6px 14px; flex: none; }
.skel { display: flex; flex-direction: column; gap: 10px; padding: 14px; }
.connect { margin: auto; display: flex; flex-direction: column; align-items: center; gap: 4px; color: var(--muted); }
.connect p { margin: 4px 0 10px; }
.sheet-foot { display: flex; justify-content: flex-end; }

@media (max-width: 640px) {
  .cal { gap: 8px; height: calc(100dvh - var(--tabbar) - 80px - env(safe-area-inset-top, 0px)); min-height: 440px; margin-bottom: calc(-20px - var(--tabbar)); }
  /* the grid uses the full width of the screen */
  .main { margin: 0 -12px; border-radius: 0; border-left: 0; border-right: 0; }
}
</style>
