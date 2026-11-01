<script setup lang="ts">
/** a Home tile as a loadout card: icon box, condensed name, status line, chips and rows; one clipped corner */
withDefaults(defineProps<{
  to?: string, icon?: string, name?: string, sub?: string, chips?: { text: string, tone?: string }[]
  more?: { text: string, sub?: string, tone?: string }[]
}>(), { to: '/', icon: 'grid', name: '', sub: '' })
</script>

<template>
  <NuxtLink :to="to" class="card topic">
    <span class="hd">
      <span class="ic"><Icon :name="icon" :size="18" /></span>
      <span class="name">{{ name }}</span>
    </span>
    <span class="line" :class="chips?.[0]?.tone">{{ chips?.[0]?.text ?? sub }}</span>
    <span v-if="chips && chips.length > 1" class="chips">
      <span v-for="c in chips.slice(1)" :key="c.text" class="pill" :class="c.tone">{{ c.text }}</span>
    </span>
    <span v-for="(r, i) in more ?? []" :key="i" class="row" :class="r.tone">{{ r.text }}<span v-if="r.sub" class="faint"> · {{ r.sub }}</span></span>
  </NuxtLink>
</template>

<style scoped>
.card {
  position: relative; display: flex; flex-direction: column; gap: 6px; height: 100%; min-width: 0; overflow: hidden; padding: 10px 12px;
  color: var(--text); text-decoration: none; background: var(--panel); border: 1px solid var(--line);
  clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 0 100%);
  font-family: "Bahnschrift", "Arial Narrow", "Roboto Condensed", system-ui, sans-serif;
}
.card:hover, .card:focus-visible { text-decoration: none; border-color: var(--accent); outline: none; }
.card:active { transform: translateY(1px); }
.hd { display: flex; align-items: center; gap: 8px; min-width: 0; }
.ic { width: 30px; height: 30px; flex: none; display: grid; place-items: center; color: var(--accent); border: 1px solid var(--line-2); }
.name { font-weight: 700; text-transform: uppercase; letter-spacing: .08em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.line { font-size: 12.5px; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.line.ok, .row.ok { color: var(--ok); } .line.warn, .row.warn { color: var(--warn); } .line.bad, .row.bad { color: var(--bad); }
.chips { display: flex; gap: 4px; flex-wrap: wrap; }
.row { font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
@container tile (max-width: 129px) {
  .card { align-items: center; justify-content: center; text-align: center; padding: 8px 4px; }
  .hd { flex-direction: column; gap: 4px; max-width: 100%; }
  .name { font-size: 11.5px; max-width: 100%; }
  .chips, .row { display: none; }
}
@container tile (max-height: 99px) { .row { display: none; } }
</style>
