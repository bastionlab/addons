<script setup lang="ts">
/** each page under an Explorer-like address bar: back / forward, "Bastion › Page" breadcrumb, a search box (opens ⌘K) */
const props = withDefaults(defineProps<{ path?: string, title?: string, icon?: string }>(), { path: '/', title: '', icon: '' })
const palette = useState('palette:open', () => false)
// pages that fill the screen get no bar (they size themselves to the viewport)
const full = computed(() => ['/chat'].includes(props.path))
const back = () => history.back()
const fwd = () => history.forward()
</script>

<template>
  <div class="w11-frame">
    <div v-if="!full" class="addr">
      <button type="button" class="nb" :aria-label="$t('skinWin11.back')" @click="back"><svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true"><path d="M13 8H3m4.5-4.5L3 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" /></svg></button>
      <button type="button" class="nb fw" :aria-label="$t('skinWin11.forward')" @click="fwd"><svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true"><path d="M3 8h10M8.5 3.5L13 8l-4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" /></svg></button>
      <div class="crumbs" role="navigation" :aria-label="$t('skinWin11.address')">
        <Icon :name="icon || 'home'" :size="15" class="ci" />
        <NuxtLink to="/" class="crumb">{{ 'Bastion' }}</NuxtLink>
        <template v-if="title && path !== '/'">
          <span class="sep">{{ '›' }}</span>
          <span class="crumb here">{{ title }}</span>
        </template>
      </div>
      <button type="button" class="srch" @click="palette = true">
        <span>{{ $t('skinWin11.search') }} {{ title || 'Bastion' }}</span><Icon name="search" :size="14" />
      </button>
    </div>
    <slot />
  </div>
</template>

<style scoped>
.addr { display: flex; align-items: center; gap: 4px; margin: 0 0 16px; }
.nb { flex: none; display: grid; place-items: center; width: 36px; height: 34px; border-radius: 6px; color: var(--text); background: transparent; border: 0; cursor: pointer; }
.nb:hover { background: rgba(255, 255, 255, .08); }
.nb:active { transform: scale(.92); }
.crumbs {
  flex: 1; min-width: 0; display: flex; align-items: center; gap: 6px; height: 34px; padding: 0 12px; margin-left: 4px;
  border-radius: 6px; background: color-mix(in srgb, var(--panel) 80%, transparent); border: 1px solid rgba(255, 255, 255, .07);
  font-size: 13px; white-space: nowrap; overflow: hidden;
}
.ci { flex: none; color: var(--accent); }
.crumb { color: var(--text); padding: 3px 6px; border-radius: 4px; overflow: hidden; text-overflow: ellipsis; }
a.crumb:hover { background: rgba(255, 255, 255, .08); text-decoration: none; }
.here { font-weight: 600; }
.sep { color: var(--faint); }
.srch {
  flex: none; display: flex; align-items: center; justify-content: space-between; gap: 10px; width: 220px; height: 34px; padding: 0 12px;
  border-radius: 6px; font: inherit; font-size: 13px; color: var(--faint); background: color-mix(in srgb, var(--panel) 80%, transparent);
  border: 1px solid rgba(255, 255, 255, .07); cursor: pointer; margin-left: 4px;
}
.srch span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.srch:hover { color: var(--text); }
@media (max-width: 760px) { .srch { display: none; } }
@media (max-width: 640px) { .addr { margin-bottom: 12px; } .fw { display: none; } }
</style>

<style>
/* page change: slide up 12 px + fade, Fluent easing */
html.skin-win11 .skin-win11-enter-active { transition: opacity .26s cubic-bezier(.1, .9, .2, 1), transform .3s cubic-bezier(.1, .9, .2, 1); }
html.skin-win11 .skin-win11-leave-active { transition: opacity .1s linear; }
html.skin-win11 .skin-win11-enter-from { opacity: 0; transform: translateY(12px); }
html.skin-win11 .skin-win11-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) {
  html.skin-win11 .skin-win11-enter-active, html.skin-win11 .skin-win11-leave-active { transition: none; }
}
</style>
