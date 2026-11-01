<script setup lang="ts">
/** a Home tile as a neon cassette: glowing icon disc, italic name, status line, chips and rows */
withDefaults(defineProps<{
  to?: string, icon?: string, name?: string, sub?: string, chips?: { text: string, tone?: string }[]
  more?: { text: string, sub?: string, tone?: string }[]
}>(), { to: '/', icon: 'grid', name: '' })
</script>

<template>
  <NuxtLink :to="to" class="cas topic">
    <span class="hd">
      <span class="disc"><Icon :name="icon" :size="17" /></span>
      <span class="name">{{ name }}</span>
    </span>
    <span class="line" :class="chips?.[0]?.tone">{{ chips?.[0]?.text ?? sub }}</span>
    <span v-if="chips && chips.length > 1" class="chips">
      <span v-for="c in chips.slice(1)" :key="c.text" class="pill" :class="c.tone">{{ c.text }}</span>
    </span>
    <span v-for="(r, i) in more ?? []" :key="i" class="row" :class="r.tone">{{ r.text }}<span v-if="r.sub" class="faint"> · {{ r.sub }}</span></span>
    <span class="tape" aria-hidden="true" />
  </NuxtLink>
</template>

<style scoped>
.cas { position: relative; display: flex; flex-direction: column; gap: 6px; height: 100%; min-width: 0; overflow: hidden; padding: 10px 12px 12px; border-radius: var(--radius); color: var(--text); text-decoration: none; background: linear-gradient(160deg, color-mix(in srgb, var(--panel-2) 92%, transparent), color-mix(in srgb, var(--panel) 94%, transparent)); border: 1px solid color-mix(in srgb, var(--accent) 45%, transparent); transition: box-shadow .2s, border-color .2s; }
.cas:hover, .cas:focus-visible { text-decoration: none; outline: none; border-color: rgb(52 230 255); box-shadow: 0 0 14px rgba(52, 230, 255, .4); }
.hd { display: flex; align-items: center; gap: 9px; min-width: 0; }
.disc { width: 30px; height: 30px; flex: none; display: grid; place-items: center; border-radius: 50%; color: var(--accent); border: 1px solid var(--accent); box-shadow: 0 0 8px color-mix(in srgb, var(--accent) 50%, transparent), inset 0 0 6px color-mix(in srgb, var(--accent) 40%, transparent); }
.name { font: italic 700 15px/1.2 "Trebuchet MS", system-ui, sans-serif; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.line { font-size: 12.5px; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.line.ok, .row.ok { color: var(--ok); } .line.warn, .row.warn { color: var(--warn); } .line.bad, .row.bad { color: var(--bad); }
.chips { display: flex; gap: 4px; flex-wrap: wrap; }
.row { font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tape { position: absolute; left: 0; right: 0; bottom: 0; height: 3px; background: linear-gradient(90deg, var(--accent), rgb(52 230 255), rgb(255 204 77)); opacity: .8; }
@container tile (max-width: 129px) {
  .cas { align-items: center; justify-content: center; text-align: center; padding: 8px 4px; }
  .hd { flex-direction: column; gap: 4px; max-width: 100%; }
  .name { font-size: 12px; max-width: 100%; }
  .chips, .row { display: none; }
}
@container tile (max-height: 99px) { .row { display: none; } }
</style>
