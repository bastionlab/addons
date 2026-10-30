<script setup lang="ts">
/**
 * Home tile as a front-page news brief: red small-caps section slug, a headline (first chip or sub), the other
 * chips as an italic standfirst, detail rows as a short list with right-aligned figures. Fills its tile.
 */
const props = defineProps<{
  to?: string, icon?: string, name?: string, sub?: string, chips?: { text: string, tone?: string }[]
  more?: { text: string, sub?: string, tone?: string }[]
}>()
const head = computed(() => props.chips?.[0] ?? (props.sub ? { text: props.sub, tone: '' } : null))
const rest = computed(() => (props.chips ?? []).slice(1))
</script>

<template>
  <NuxtLink :to="to ?? '/'" class="topic bcard">
    <span class="slug"><Icon :name="icon ?? 'grid'" :size="20" /><span class="sn">{{ name }}</span></span>
    <span v-if="head" class="hl" :class="head.tone">{{ head.text }}</span>
    <span v-if="rest.length" class="stand">
      <span v-for="(c, i) in rest" :key="c.text" :class="c.tone">{{ i ? ` · ${c.text}` : c.text }}</span>
    </span>
    <span v-if="more?.length" class="more">
      <span v-for="(r, i) in more" :key="i" class="row">
        <span class="rt" :class="r.tone">{{ r.text }}</span><span v-if="r.sub" class="rs">{{ r.sub }}</span>
      </span>
    </span>
  </NuxtLink>
</template>

<style scoped>
.bcard {
  display: flex; flex-direction: column; gap: 4px; height: 100%; min-width: 0; overflow: hidden; padding: 8px 12px 10px;
  border-top: 3px double var(--text); background: var(--bs-grain), var(--panel); color: var(--text); text-decoration: none; font-family: var(--bs-serif);
}
.bcard:hover { text-decoration: none; }
.bcard:hover .hl { text-decoration: underline; text-decoration-thickness: 1px; text-underline-offset: 3px; }
.bcard:active { background: var(--bs-grain), var(--panel-2); }
.slug { display: flex; align-items: center; gap: 6px; min-width: 0; color: var(--accent); font-variant: small-caps; text-transform: lowercase; letter-spacing: .1em; font-size: 13px; font-weight: 700; }
.slug .icon { flex: none; }
.sn { min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hl { color: var(--text); font-family: var(--bs-disp); font-weight: 800; font-size: 19px; line-height: 1.15; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.hl.warn { color: var(--warn); } .hl.bad { color: var(--bad); }
.stand { font-style: italic; font-size: 13px; color: var(--muted); max-height: 38px; overflow: hidden; }
.stand .warn { color: var(--warn); } .stand .bad { color: var(--bad); } .stand .ok { color: var(--ok); }
.more { display: none; flex-direction: column; flex: 1; min-height: 0; overflow: hidden; margin-top: 2px; padding-top: 4px; border-top: 1px solid var(--line-2); }
.row { display: flex; align-items: baseline; gap: 8px; padding: 2px 0; font-size: 13.5px; min-width: 0; border-bottom: 1px dotted var(--line); }
.rt { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rt::before { content: "■ "; font-size: .6em; vertical-align: .2em; color: var(--faint); }
.rt.ok { color: var(--ok); } .rt.warn { color: var(--warn); } .rt.bad { color: var(--bad); }
.rs { margin-left: auto; flex: none; font-size: 12.5px; color: var(--faint); font-style: italic; }

@container tile (max-height: 99px) {
  .bcard { justify-content: center; gap: 2px; padding: 6px 10px; }
  .stand { display: none; }
  .hl { font-size: 15px; -webkit-line-clamp: 1; }
}
@container tile (min-height: 100px) { .more { display: flex; } }
@container tile (min-height: 180px) and (min-width: 240px) { .hl { font-size: 24px; } }
@container tile (max-width: 129px) {
  .bcard { align-items: center; justify-content: center; text-align: center; padding: 6px; }
  .stand, .more { display: none; }
  .slug { flex-direction: column; gap: 3px; font-size: 12px; max-width: 100%; }
  .hl { font-size: 13px; max-width: 100%; }
}
</style>
