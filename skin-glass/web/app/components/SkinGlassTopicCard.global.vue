<script setup lang="ts">
/**
 * Home tile as an iOS widget: tinted glass with a colour of its own, app icon top-left, status dot top-right,
 * the headline (first chip or sub) in large type, then chips and detail rows as room allows (HomeItem's `tile` container).
 */
const props = defineProps<{
  to?: string, icon?: string, name?: string, sub?: string, chips?: { text: string, tone?: string }[]
  more?: { text: string, sub?: string, tone?: string }[]
}>()
const hue = computed(() => { let h = 0; for (const c of props.to ?? props.name ?? '') h = (h * 31 + c.charCodeAt(0)) % 360; return h })
const head = computed(() => props.chips?.[0] ?? (props.sub ? { text: props.sub, tone: '' } : null))
const status = computed(() => (props.chips?.some(c => c.tone) ? (props.chips.find(c => c.tone === 'bad' || c.tone === 'warn')?.tone ?? 'ok') : ''))
</script>

<template>
  <NuxtLink :to="to ?? '/'" class="topic gw" :style="{ '--h': hue }">
    <span class="top">
      <span class="ai"><Icon :name="icon ?? 'grid'" :size="18" /></span>
      <span class="nm">{{ name }}</span>
      <span v-if="status" class="st" :class="status" />
    </span>
    <span v-if="head" class="big" :class="head.tone">{{ head.text }}</span>
    <span v-if="chips && chips.length > 1" class="chips">
      <span v-for="c in chips.slice(1)" :key="c.text" class="pill" :class="c.tone">{{ c.text }}</span>
    </span>
    <span v-if="more?.length" class="more">
      <span v-for="(r, i) in more" :key="i" class="row">
        <span class="rt" :class="r.tone">{{ r.text }}</span><span v-if="r.sub" class="rs">{{ r.sub }}</span>
      </span>
    </span>
  </NuxtLink>
</template>

<style scoped>
.gw {
  position: relative; z-index: 0; display: flex; flex-direction: column; gap: 6px; height: 100%; min-width: 0; overflow: hidden;
  padding: 12px 14px; border-radius: 22px; color: var(--text); text-decoration: none;
  background: linear-gradient(150deg, hsl(var(--h) 70% 55% / .28), hsl(calc(var(--h) + 50) 70% 40% / .12) 60%, rgba(255, 255, 255, .04));
  border: 1px solid rgba(255, 255, 255, .14);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .22), 0 12px 30px rgba(0, 0, 0, .28);
  backdrop-filter: blur(22px) saturate(170%); -webkit-backdrop-filter: blur(22px) saturate(170%);
  transition: transform .4s cubic-bezier(.34, 1.56, .64, 1);
}
.gw:hover { text-decoration: none; }
.gw:active { transform: scale(.97); }
.top { display: flex; align-items: center; gap: 9px; min-width: 0; }
.ai {
  display: grid; place-items: center; width: 30px; height: 30px; flex: none; border-radius: 9px; color: rgba(255, 255, 255, .96);
  background: linear-gradient(145deg, hsl(var(--h) 85% 64%), hsl(calc(var(--h) + 40) 75% 46%));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .45), 0 4px 10px rgba(0, 0, 0, .25);
}
.nm { flex: 1; min-width: 0; font-size: 13px; font-weight: 600; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.st { width: 8px; height: 8px; flex: none; border-radius: 50%; background: var(--ok); box-shadow: 0 0 10px var(--ok); }
.st.warn { background: var(--warn); box-shadow: 0 0 10px var(--warn); }
.st.bad { background: var(--bad); box-shadow: 0 0 10px var(--bad); }
.big { font-size: 20px; font-weight: 700; letter-spacing: -.02em; line-height: 1.15; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.big.ok { color: var(--ok); } .big.warn { color: var(--warn); } .big.bad { color: var(--bad); }
.chips { display: flex; flex-wrap: wrap; gap: 4px; min-width: 0; max-height: 46px; overflow: hidden; }
.more { display: none; flex-direction: column; flex: 1; min-height: 0; overflow: hidden; margin-top: 2px; padding-top: 6px; border-top: 1px solid rgba(255, 255, 255, .1); }
.row { display: flex; gap: 8px; align-items: baseline; padding: 2px 0; font-size: 13px; min-width: 0; }
.rt { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rt.ok { color: var(--ok); } .rt.warn { color: var(--warn); } .rt.bad { color: var(--bad); }
.rs { margin-left: auto; flex: none; font-size: 12px; color: var(--faint); }

/* short tile: one line, icon + name + headline */
@container tile (max-height: 99px) {
  .gw { flex-direction: row; flex-wrap: wrap; align-items: center; align-content: center; column-gap: 10px; row-gap: 2px; padding: 8px 12px; }
  .top { flex: 1 1 100%; }
  .big { flex: 1 1 100%; font-size: 15px; padding-left: 39px; margin-top: -8px; }
  .chips { display: none; }
}
@container tile (min-height: 100px) { .more { display: flex; } }
@container tile (min-height: 180px) and (min-width: 240px) { .big { font-size: 26px; } }
/* narrow: icon over name, centred */
@container tile (max-width: 129px) {
  .gw { align-items: center; justify-content: center; text-align: center; padding: 8px 6px; flex-wrap: nowrap; flex-direction: column; }
  .top { flex-direction: column; flex: none; gap: 5px; max-width: 100%; }
  .nm { font-size: 12px; max-width: 100%; }
  .st { position: absolute; top: 8px; right: 8px; }
  .big { font-size: 13px; padding: 0; margin: 0; max-width: 100%; }
  .chips, .more { display: none; }
}
@media (prefers-reduced-motion: reduce) { .gw { transition: none; } }
/* phone budget (SKINS.md): no backdrop-filter on large layers, a denser translucent fill instead */
@media (max-width: 640px), (pointer: coarse) {
  .gw { backdrop-filter: none; -webkit-backdrop-filter: none; background: linear-gradient(150deg, hsl(var(--h) 70% 55% / .28), hsl(calc(var(--h) + 50) 70% 40% / .12) 60%, rgba(255, 255, 255, .04)), color-mix(in srgb, var(--panel) 92%, transparent); }
}
</style>
