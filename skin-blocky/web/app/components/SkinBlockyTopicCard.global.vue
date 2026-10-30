<script setup lang="ts">
/** Home tile as a stone button with the page's item in a slot; the headline reads like an item tooltip */
const props = withDefaults(defineProps<{
  to?: string, icon?: string, name?: string, sub?: string, chips?: { text: string, tone?: string }[]
  more?: { text: string, sub?: string, tone?: string }[]
}>(), { to: '/', icon: 'grid', name: '' })
const head = computed(() => props.chips?.[0] ?? (props.sub ? { text: props.sub, tone: '' } : null))
</script>

<template>
  <NuxtLink :to="to" class="topic btile">
    <span class="hd">
      <span class="slot"><Icon :name="icon" :size="18" /></span>
      <span class="nm">{{ name }}</span>
    </span>
    <span v-if="head" class="tip" :class="head.tone">{{ head.text }}</span>
    <span v-if="chips && chips.length > 1" class="chips">
      <span v-for="c in chips.slice(1)" :key="c.text" class="pill" :class="c.tone">{{ c.text }}</span>
    </span>
    <span v-if="more?.length" class="more">
      <span v-for="(r, i) in more" :key="i" class="row"><span class="rt" :class="r.tone">{{ r.text }}</span><span v-if="r.sub" class="rs">{{ r.sub }}</span></span>
    </span>
  </NuxtLink>
</template>

<style scoped>
.btile {
  display: flex; flex-direction: column; gap: 7px; height: 100%; min-width: 0; overflow: hidden; padding: 9px 11px; color: var(--text); text-decoration: none;
  background: linear-gradient(90deg, rgba(255, 255, 255, .04) 50%, rgba(0, 0, 0, .04) 0) 0 0 / 8px 8px, var(--panel);
  border: 2px solid rgba(0, 0, 0, 1); box-shadow: inset 3px 3px 0 rgba(255, 255, 255, .3), inset -3px -3px 0 rgba(0, 0, 0, .38);
}
.btile:hover { text-decoration: none; background: linear-gradient(90deg, rgba(255, 255, 255, .04) 50%, rgba(0, 0, 0, .04) 0) 0 0 / 8px 8px, rgba(126, 134, 190, 1); }
.btile:active { transform: scale(1.02, .94); }
.hd { display: flex; align-items: center; gap: 8px; min-width: 0; }
.slot { flex: none; display: grid; place-items: center; width: 32px; height: 32px; background: rgba(139, 139, 139, .6); box-shadow: inset 2px 2px 0 rgba(40, 40, 40, 1), inset -2px -2px 0 rgba(230, 230, 230, .85); }
.slot :deep(svg) { filter: drop-shadow(2px 2px 0 rgba(40, 40, 40, 1)); }
.nm { min-width: 0; font-size: 14px; font-weight: 900; text-transform: uppercase; letter-spacing: .04em; text-shadow: 2px 2px 0 rgba(40, 40, 40, 1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tip {
  align-self: flex-start; max-width: 100%; padding: 2px 6px; font-size: 12.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text);
  background: rgba(16, 0, 16, .85); border: 1px solid rgba(42, 10, 94, 1); box-shadow: inset 0 0 0 1px rgba(90, 42, 168, 1);
}
.tip.ok, .rt.ok { color: var(--ok); } .tip.warn, .rt.warn { color: var(--warn); } .tip.bad, .rt.bad { color: var(--bad); }
.chips { display: flex; flex-wrap: wrap; gap: 4px; }
.more { display: none; flex-direction: column; min-height: 0; overflow: hidden; }
.row { display: flex; gap: 8px; align-items: baseline; padding: 2px 0; font-size: 12.5px; min-width: 0; text-shadow: 1px 1px 0 rgba(40, 40, 40, 1); border-bottom: 2px solid rgba(0, 0, 0, .18); }
.rt { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rs { margin-left: auto; flex: none; font-size: 11.5px; color: var(--muted); }
@container tile (max-height: 99px) { .chips { display: none; } .btile { padding: 6px 9px; } }
@container tile (min-height: 100px) { .more { display: flex; } }
@container tile (max-width: 129px) {
  .btile { align-items: center; padding: 7px 5px; gap: 4px; }
  .hd { flex-direction: column; gap: 3px; }
  .nm { font-size: 11px; max-width: 100%; text-align: center; }
  .tip { align-self: center; font-size: 11px; }
  .chips, .more { display: none; }
}
</style>
