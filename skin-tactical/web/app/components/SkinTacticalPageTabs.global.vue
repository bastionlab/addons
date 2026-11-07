<script setup lang="ts">
/**
 * The page's sections as one condensed uppercase row: the open one underlined amber. Same behaviour as PageTabs.vue.
 */
const props = defineProps<{ tabs: { key: string, label: string, icon?: string, badge?: number | string, tone?: 'ok' | 'warn' | 'bad' }[] }>()
const model = defineModel<string>({ required: true })
const { anchor, strip, nav, edge, measure, pick } = usePageTabs({ count: () => props.tabs.length, model, autoCompact: true })
</script>

<template>
  <div class="tac-ptabs-wrap">
    <div ref="anchor" />
    <nav ref="nav" class="tac-ptabs" :class="{ l: edge.l, r: edge.r }">
      <div ref="strip" class="strip" role="tablist" @scroll.passive="measure">
        <button
          v-for="t in tabs" :key="t.key" type="button" role="tab" class="cat" :class="{ on: model === t.key, ico: !!t.icon }"
          :aria-selected="model === t.key" :aria-label="t.label" :title="t.label" @click="pick(t.key)"
        >
          <Icon v-if="t.icon" :name="t.icon" :size="15" class="ic" />
          <span class="lb">{{ t.label }}</span>
          <span v-if="t.badge" class="bdg" :class="t.tone ?? 'warn'">{{ t.badge }}</span>
        </button>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.tac-ptabs-wrap { display: contents; }
.tac-ptabs {
  position: sticky; top: var(--ptabs-top, env(safe-area-inset-top, 0px)); z-index: 20; margin: 0 0 16px;
  display: flex; background: color-mix(in srgb, var(--bg) 92%, transparent);
  border-bottom: 1px solid var(--line-2);
  font-family: "Bahnschrift", "Arial Narrow", "Roboto Condensed", system-ui, sans-serif; text-transform: uppercase; letter-spacing: .06em;
}
.strip { flex: 1; min-width: 0; display: flex; gap: 4px; overflow-x: auto; scrollbar-width: none; padding: 0 4px; overscroll-behavior-x: contain; }
.strip::-webkit-scrollbar { display: none; }
.tac-ptabs.l .strip { mask-image: linear-gradient(to right, transparent, black 28px); }
.tac-ptabs.r .strip { mask-image: linear-gradient(to left, transparent, black 28px); }
.tac-ptabs.l.r .strip { mask-image: linear-gradient(to right, transparent, black 28px, black calc(100% - 28px), transparent); }
.cat {
  position: relative; flex: none; display: inline-flex; align-items: center; gap: 7px; min-height: 38px; padding: 4px 12px;
  border: 0; border-bottom: 2px solid transparent; border-radius: 0; background: transparent;
  color: var(--muted); font: inherit; font-size: 13px; font-weight: 600; white-space: nowrap; cursor: pointer;
}
.cat:hover, .cat:focus-visible { color: var(--text); outline: none; }
.cat.on { color: var(--text); border-bottom-color: var(--accent); }
.cat.on .ic { color: var(--accent); }
.bdg { min-width: 18px; padding: 0 5px; font-size: 11px; line-height: 17px; text-align: center; font-weight: 700; color: var(--bg); background: var(--warn); }
.bdg.bad { background: var(--bad); }
.bdg.ok { background: var(--ok); }
@media (max-width: 640px) {
  .tac-ptabs { margin: 0 -12px 12px; }
  .cat { min-height: 40px; font-size: 13px; }
  .tac-ptabs.is-compact .cat.ico:not(.on) .lb { display: none; }
  .tac-ptabs.is-compact .cat.ico:not(.on) { min-width: 40px; justify-content: center; }
}
</style>
