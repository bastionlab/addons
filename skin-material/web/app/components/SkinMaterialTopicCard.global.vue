<script setup lang="ts">
/** a Home tile as an M3 elevated card: the icon in a tonal circle, name + first status line, then chips and detail rows when tall */
withDefaults(defineProps<{
  to?: string, icon?: string, name?: string, sub?: string, chips?: { text: string, tone?: string }[]
  more?: { text: string, sub?: string, tone?: string }[]
}>(), { to: '/', icon: 'grid', name: '' })
</script>

<template>
  <NuxtLink :to="to" class="m3-topic m3-rip">
    <span class="hd">
      <span class="ic"><Icon :name="icon" :size="20" /></span>
      <span class="txt">
        <span class="name">{{ name }}</span>
        <span class="line" :class="chips?.[0]?.tone">{{ chips?.[0]?.text ?? sub }}</span>
      </span>
    </span>
    <span v-if="chips && chips.length > 1" class="chips">
      <span v-for="c in chips.slice(1)" :key="c.text" class="pill" :class="c.tone">{{ c.text }}</span>
    </span>
    <span v-if="more?.length" class="more">
      <span v-for="(r, i) in more" :key="i" class="row">
        <span class="rt" :class="r.tone">{{ r.text }}</span>
        <span v-if="r.sub" class="rs">{{ r.sub }}</span>
      </span>
    </span>
  </NuxtLink>
</template>

<style scoped>
.m3-topic { position: relative; display: flex; flex-direction: column; justify-content: center; gap: 8px; height: 100%; min-width: 0; overflow: hidden; padding: 10px 14px; border-radius: 16px; color: var(--text); text-decoration: none; background: color-mix(in srgb, var(--accent) 5%, var(--panel)); box-shadow: 0 1px 2px rgba(0, 0, 0, .3), 0 1px 3px 1px rgba(0, 0, 0, .15); transition: box-shadow .2s, background-color .2s; }
.m3-topic:hover { text-decoration: none; }
@media (hover: hover) { .m3-topic:hover { background: color-mix(in srgb, var(--accent) 9%, var(--panel)); box-shadow: 0 1px 2px rgba(0, 0, 0, .3), 0 2px 6px 2px rgba(0, 0, 0, .15); } }
.hd { display: flex; align-items: center; gap: 12px; min-width: 0; }
.ic { display: grid; place-items: center; width: 40px; height: 40px; flex: none; border-radius: 50%; background: var(--m3-sec); color: var(--m3-on-sec); }
.txt { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.name { font-size: 16px; font-weight: 500; letter-spacing: .15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.line { font-size: 12.5px; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.line.ok { color: var(--ok); } .line.warn { color: var(--warn); } .line.bad { color: var(--bad); }
.chips { display: none; flex-wrap: wrap; gap: 4px; }
.more { display: none; flex: 1; min-height: 0; flex-direction: column; overflow: hidden; border-top: 1px solid var(--line); padding-top: 6px; }
.row { display: flex; gap: 10px; align-items: baseline; padding: 3px 0; min-width: 0; font-size: 13px; }
.rt { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rt.ok { color: var(--ok); } .rt.warn { color: var(--warn); } .rt.bad { color: var(--bad); }
.rs { margin-left: auto; flex: none; font-size: 12px; color: var(--faint); }
@container tile (min-height: 100px) {
  .m3-topic { justify-content: flex-start; padding: 14px 16px; }
  .chips { display: flex; }
  .more { display: flex; }
}
@container tile (max-width: 129px) {
  .m3-topic { align-items: center; padding: 6px; text-align: center; }
  .hd { flex-direction: column; gap: 4px; max-width: 100%; }
  .ic { width: 32px; height: 32px; }
  .txt { align-items: center; max-width: 100%; }
  .name { font-size: 12px; }
  .line, .chips, .more { display: none; }
}
@media (max-width: 640px) { .m3-topic { padding: 8px 10px; } .ic { width: 34px; height: 34px; } .hd { gap: 10px; } .name { font-size: 14.5px; } }
</style>
