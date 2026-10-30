<script setup lang="ts">
/** A Home tile as a book plate: double gold rule, the page icon and name in gold small caps, the status in italics */
withDefaults(defineProps<{
  to?: string, icon?: string, name?: string, sub?: string, chips?: { text: string, tone?: string }[]
  more?: { text: string, sub?: string, tone?: string }[]
}>(), { to: '/', icon: 'grid', name: '' })
</script>

<template>
  <NuxtLink :to="to" class="gm-card">
    <span class="hd">
      <Icon :name="icon" :size="20" class="ic" />
      <span class="txt">
        <span class="name">{{ name }}</span>
        <span class="line" :class="chips?.[0]?.tone">{{ chips?.[0]?.text ?? sub }}</span>
      </span>
    </span>
    <span v-if="chips && chips.length > 1" class="chips">
      <span v-for="c in chips.slice(1)" :key="c.text" class="pill" :class="c.tone">{{ c.text }}</span>
    </span>
    <span v-if="more?.length" class="more">
      <span v-for="(r, i) in more" :key="i" class="row"><span class="rt" :class="r.tone">{{ r.text }}</span><span v-if="r.sub" class="rs">{{ r.sub }}</span></span>
    </span>
  </NuxtLink>
</template>

<style scoped>
.gm-card {
  display: flex; flex-direction: column; justify-content: center; gap: 8px; height: 100%; min-width: 0; overflow: hidden;
  padding: 8px 12px; border-radius: 3px; color: var(--text); text-decoration: none;
  background: color-mix(in srgb, var(--panel) 96%, transparent);
  border: 1px solid color-mix(in srgb, var(--warn) 32%, transparent);
  outline: 1px solid color-mix(in srgb, var(--warn) 12%, transparent); outline-offset: -5px;
  transition: border-color .2s;
}
.gm-card:hover { text-decoration: none; border-color: var(--warn); }
.hd { display: flex; align-items: center; gap: 10px; min-width: 0; }
.ic { color: var(--warn); }
.txt { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.name { font: 600 13px/1.3 Georgia, "Palatino Linotype", serif; letter-spacing: .12em; text-transform: uppercase; color: var(--warn); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.line { font-size: 12.5px; font-style: italic; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.line.ok { color: var(--ok); } .line.warn { color: var(--warn); } .line.bad { color: var(--bad); }
.chips { display: none; flex-wrap: wrap; gap: 4px; }
.more { display: none; flex: 1; min-height: 0; flex-direction: column; overflow: hidden; border-top: 1px solid color-mix(in srgb, var(--warn) 22%, transparent); padding-top: 6px; }
.row { display: flex; gap: 10px; align-items: baseline; padding: 3px 0; min-width: 0; font-size: 13px; }
.rt { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rt.ok { color: var(--ok); } .rt.warn { color: var(--warn); } .rt.bad { color: var(--bad); }
.rs { margin-left: auto; flex: none; font-size: 12px; color: var(--faint); }
@container tile (min-height: 100px) { .gm-card { justify-content: flex-start; padding: 14px 14px 12px; } .chips, .more { display: flex; } }
@container tile (max-width: 129px) {
  .gm-card { align-items: center; padding: 6px; text-align: center; }
  .hd { flex-direction: column; gap: 4px; max-width: 100%; }
  .txt { align-items: center; max-width: 100%; }
  .name { font-size: 10.5px; letter-spacing: .06em; }
  .line, .chips, .more { display: none; }
}
</style>
