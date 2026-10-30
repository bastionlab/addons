<script setup lang="ts">
/** a Home tile as a Fluent widget card: tinted icon square, name, status line, chips and detail rows; reveal-glow on hover */
withDefaults(defineProps<{
  to?: string, icon?: string, name?: string, sub?: string, chips?: { text: string, tone?: string }[]
  more?: { text: string, sub?: string, tone?: string }[]
}>(), { to: '/' })
</script>

<template>
  <NuxtLink :to="to" class="topic widget">
    <span class="hd">
      <span class="ti"><Icon :name="icon || 'grid'" :size="18" /></span>
      <span class="txt">
        <span class="name">{{ name }}</span>
        <span class="line" :class="chips?.[0]?.tone">{{ chips?.[0]?.text ?? sub }}</span>
      </span>
    </span>
    <span v-if="chips && chips.length > 1" class="chips">
      <span v-for="c in chips.slice(1)" :key="c.text" class="pill" :class="c.tone">{{ c.text }}</span>
    </span>
    <span v-if="more?.length" class="more">
      <span v-for="(m, i) in more" :key="i" class="row"><span class="rt" :class="m.tone">{{ m.text }}</span><span v-if="m.sub" class="rs">{{ m.sub }}</span></span>
    </span>
  </NuxtLink>
</template>

<style scoped>
.widget {
  display: flex; flex-direction: column; gap: 8px; height: 100%; min-width: 0; overflow: hidden; padding: 12px 14px;
  color: var(--text); text-decoration: none; border-radius: 8px; border: 1px solid rgba(255, 255, 255, .07);
  background: color-mix(in srgb, var(--panel) 88%, transparent); box-shadow: 0 2px 6px rgba(0, 0, 0, .2);
  transition: background .2s, transform .2s cubic-bezier(.1, .9, .2, 1), border-color .2s;
}
.widget:hover { text-decoration: none; background: color-mix(in srgb, var(--panel-2) 92%, transparent); border-color: rgba(255, 255, 255, .14); }
.widget:active { transform: scale(.98); }
.hd { display: flex; align-items: center; gap: 12px; min-width: 0; }
.ti { flex: none; display: grid; place-items: center; width: 34px; height: 34px; border-radius: 6px; color: var(--accent); background: linear-gradient(160deg, color-mix(in srgb, var(--accent) 25%, transparent), color-mix(in srgb, var(--accent) 6%, transparent)); }
.txt { display: flex; flex-direction: column; min-width: 0; }
.name { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.line { font-size: 12px; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.line.ok { color: var(--ok); } .line.warn { color: var(--warn); } .line.bad { color: var(--bad); }
.chips { display: flex; gap: 4px; flex-wrap: wrap; max-height: 48px; overflow: hidden; }
.more { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; border-top: 1px solid rgba(255, 255, 255, .06); padding-top: 4px; }
.row { display: flex; gap: 10px; padding: 2px 0; font-size: 12.5px; min-width: 0; }
.rt { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rt.ok { color: var(--ok); } .rt.warn { color: var(--warn); } .rt.bad { color: var(--bad); }
.rs { margin-left: auto; flex: none; color: var(--faint); font-size: 12px; }
@container tile (max-width: 129px) {
  .widget { align-items: center; justify-content: center; text-align: center; padding: 8px 6px; }
  .hd { flex-direction: column; gap: 6px; }
  .name { font-size: 12px; }
  .line, .chips, .more { display: none; }
}
@container tile (max-height: 99px) { .chips, .more { display: none; } .widget { justify-content: center; } }
</style>
