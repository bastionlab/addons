<script setup lang="ts">
/**
 * Panel as a Mica window: title row with minimise (= fold, same remembered state as the stock Panel) and
 * maximise (spans the whole grid row and lifts the window). Tapping the title row folds too.
 */
const props = withDefaults(defineProps<{ title?: string, sub?: string, id?: string, fold?: 'open' | 'closed' | 'phone' }>(), { title: '', fold: 'open' })
const key = props.id ? `panel:${props.id}` : `panel:${useRoute().path}:${props.title}`
const phone = typeof window !== 'undefined' && window.matchMedia('(max-width: 640px)').matches
const open = ref(props.fold === 'open' || (props.fold === 'phone' && !phone))
try { const v = localStorage.getItem(key); if (v) open.value = v === '1' } catch {}
const max = ref(false)
function toggle() {
  open.value = !open.value
  try { localStorage.setItem(key, open.value ? '1' : '0') } catch {}
}
function maximise() { max.value = !max.value; if (max.value && !open.value) toggle() }
</script>

<template>
  <section :id="id" class="mica panel" :class="{ folded: !open, max }">
    <header class="bar" @click="toggle">
      <h2>{{ title }}</h2>
      <span v-if="sub" class="sub">{{ sub }}</span>
      <div v-if="open" class="actions" @click.stop><slot name="actions" /></div>
      <span class="ctls" @click.stop>
        <button type="button" class="ctl" :aria-label="open ? $t('skinWin11.minimise') : $t('skinWin11.restore')" @click="toggle">
          <svg v-if="open" viewBox="0 0 10 10" width="10" height="10" aria-hidden="true"><path d="M0 5.5h10" stroke="currentColor" stroke-width="1" /></svg>
          <svg v-else viewBox="0 0 10 10" width="10" height="10" aria-hidden="true"><path d="M1 6.5l4-4 4 4" fill="none" stroke="currentColor" stroke-width="1" /></svg>
        </button>
        <button type="button" class="ctl" :aria-label="max ? $t('skinWin11.unmaximise') : $t('skinWin11.maximise')" @click="maximise">
          <svg v-if="!max" viewBox="0 0 10 10" width="10" height="10" aria-hidden="true"><rect x=".5" y=".5" width="9" height="9" rx="1.5" fill="none" stroke="currentColor" stroke-width="1" /></svg>
          <svg v-else viewBox="0 0 10 10" width="10" height="10" aria-hidden="true"><rect x=".5" y="2.5" width="7" height="7" rx="1.2" fill="none" stroke="currentColor" stroke-width="1" /><path d="M2.5 2.5V1.8c0-.7.6-1.3 1.3-1.3h4.4c.7 0 1.3.6 1.3 1.3v4.4c0 .7-.6 1.3-1.3 1.3h-.7" fill="none" stroke="currentColor" stroke-width="1" /></svg>
        </button>
      </span>
    </header>
    <Transition name="w11-fold"><div v-if="open" class="body"><slot /></div></Transition>
  </section>
</template>

<style scoped>
.mica {
  position: relative; min-width: 0; scroll-margin-top: 16px; border-radius: 8px; overflow: hidden;
  background: linear-gradient(160deg, color-mix(in srgb, var(--panel) 90%, var(--accent)) 0%, var(--panel) 45%, color-mix(in srgb, var(--panel) 94%, var(--bg)) 100%);
  border: 1px solid rgba(255, 255, 255, .07); box-shadow: 0 2px 6px rgba(0, 0, 0, .22);
  transition: box-shadow .25s cubic-bezier(.1, .9, .2, 1);
}
.folded { align-self: start; }
/* no transform here: a transformed ancestor would trap the panel's own fixed overlays (sheets, dialogs) inside it */
.max { grid-column: 1 / -1; box-shadow: 0 18px 48px rgba(0, 0, 0, .5), 0 0 0 1px color-mix(in srgb, var(--accent) 35%, transparent); z-index: 1; }
.bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; min-height: 38px; padding: 0 0 0 14px; cursor: default; user-select: none; }
h2 { font-size: 13.5px; font-weight: 600; margin: 0; color: var(--text); }
.sub { font-size: 12px; color: var(--faint); min-width: 0; }
.actions { margin-left: auto; display: flex; gap: 6px; flex-wrap: wrap; padding: 4px 0; }
.ctls { margin-left: auto; display: flex; align-self: flex-start; }
.actions + .ctls { margin-left: 0; }
.ctl { display: grid; place-items: center; width: 44px; height: 34px; padding: 0; color: var(--muted); background: transparent; border: 0; cursor: pointer; }
.ctl:hover { background: rgba(255, 255, 255, .08); color: var(--text); }
.ctl:last-child:hover { background: color-mix(in srgb, var(--accent) 25%, transparent); }
.body { padding: 4px 16px 16px; }
.w11-fold-enter-active { transition: opacity .25s, transform .25s cubic-bezier(.1, .9, .2, 1); }
.w11-fold-enter-from { opacity: 0; transform: translateY(-6px); }
@media (max-width: 640px) { .body { padding: 2px 12px 14px; } .bar { padding-left: 12px; } .ctl { width: 40px; height: 36px; } }
@media (prefers-reduced-motion: reduce) { .mica, .w11-fold-enter-active { transition: none; } }
</style>
