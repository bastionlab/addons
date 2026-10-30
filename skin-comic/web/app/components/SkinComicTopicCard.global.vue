<script setup lang="ts">
/** Home tile as a mini comic cover: coloured title strip with the name, icon in a burst, the headline in a speech bubble */
const props = defineProps<{
  to?: string, icon?: string, name?: string, sub?: string, chips?: { text: string, tone?: string }[]
  more?: { text: string, sub?: string, tone?: string }[]
}>()
const STRIPS = ['var(--comic-red)', 'var(--comic-blue)', 'var(--line-2)', 'var(--ok)']
const strip = computed(() => { let h = 0; for (const c of props.to ?? props.name ?? '') h = (h * 31 + c.charCodeAt(0)) >>> 0; return STRIPS[h % STRIPS.length] })
const head = computed(() => props.chips?.[0] ?? (props.sub ? { text: props.sub, tone: '' } : null))
</script>

<template>
  <NuxtLink :to="to ?? '/'" class="topic ccov" :style="{ '--strip': strip }">
    <span class="strip">
      <span class="ic"><Icon :name="icon ?? 'grid'" :size="16" /></span>
      <span class="nm">{{ name }}</span>
    </span>
    <span class="body">
      <span v-if="head" class="say" :class="head.tone">{{ head.text }}</span>
      <span v-if="chips && chips.length > 1" class="chips">
        <span v-for="c in chips.slice(1)" :key="c.text" class="pill" :class="c.tone">{{ c.text }}</span>
      </span>
      <span v-if="more?.length" class="more">
        <span v-for="(r, i) in more" :key="i" class="row"><span class="rt" :class="r.tone">{{ r.text }}</span><span v-if="r.sub" class="rs">{{ r.sub }}</span></span>
      </span>
    </span>
  </NuxtLink>
</template>

<style scoped>
.ccov {
  display: flex; flex-direction: column; height: 100%; min-width: 0; overflow: hidden; color: var(--text); text-decoration: none;
  background: var(--panel); border: 3px solid var(--line-2); box-shadow: 4px 4px 0 var(--line-2); transition: transform .12s, box-shadow .12s;
}
.ccov:hover { text-decoration: none; transform: translate(-2px, -2px); box-shadow: 6px 6px 0 var(--line-2); }
.ccov:active { transform: translate(2px, 2px); box-shadow: 1px 1px 0 var(--line-2); }
.strip { display: flex; align-items: center; gap: 8px; padding: 5px 8px; flex: none; background: var(--strip); border-bottom: 3px solid var(--line-2); }
.ic { display: grid; place-items: center; width: 28px; height: 28px; flex: none; color: var(--line-2); background: var(--comic-yellow); border: 2px solid var(--line-2); border-radius: 50%; }
.nm { min-width: 0; font-size: 14px; font-weight: 900; font-style: italic; text-transform: uppercase; letter-spacing: .02em; color: var(--panel); -webkit-text-stroke: .6px var(--line-2); text-shadow: 1.5px 1.5px 0 var(--line-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.body { display: flex; flex-direction: column; gap: 8px; padding: 8px 10px 8px; min-height: 0; flex: 1; overflow: hidden; background-image: radial-gradient(circle, rgba(0, 0, 0, .07) 1px, transparent 1.4px); background-size: 7px 7px; }
.say {
  position: relative; align-self: flex-start; max-width: 100%; padding: 4px 10px; font-size: 13px; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  background: var(--panel); border: 2px solid var(--line-2); border-radius: 14px;
}
.say.ok { color: var(--ok); } .say.warn { color: var(--warn); } .say.bad { color: var(--bad); }
.chips { display: flex; flex-wrap: wrap; gap: 4px; }
.more { display: none; flex-direction: column; min-height: 0; overflow: hidden; }
.row { display: flex; gap: 8px; align-items: baseline; padding: 2px 0; font-size: 12.5px; font-weight: 600; min-width: 0; border-bottom: 1.5px dashed color-mix(in srgb, var(--line-2) 30%, transparent); }
.rt { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rt.ok { color: var(--ok); } .rt.warn { color: var(--warn); } .rt.bad { color: var(--bad); }
.rs { margin-left: auto; flex: none; font-size: 11.5px; color: var(--faint); }
@container tile (max-height: 99px) { .chips { display: none; } .body { padding: 5px 8px; } }
@container tile (min-height: 100px) { .more { display: flex; } }
@container tile (max-width: 129px) {
  .strip { flex-direction: column; gap: 3px; padding: 6px 4px; }
  .nm { font-size: 11px; max-width: 100%; text-align: center; }
  .body { align-items: center; padding: 5px 4px; }
  .say { font-size: 11px; padding: 2px 6px; }
  .chips, .more { display: none; }
}
@media (prefers-reduced-motion: reduce) { .ccov { transition: none; } }
</style>
