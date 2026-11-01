<script setup lang="ts">
/** a Home tile as a sticker: thick white border, soft shadow, a peeling corner and a wiggle when touched */
const props = withDefaults(defineProps<{
  to?: string, icon?: string, name?: string, sub?: string, chips?: { text: string, tone?: string }[]
  more?: { text: string, sub?: string, tone?: string }[]
}>(), { to: '/' })
const hue = computed(() => `hsl(${[...(props.name || 'x')].reduce((s, c) => s + c.charCodeAt(0) * 37, 0) % 360} 85% 90%)`)
</script>

<template>
  <NuxtLink :to="to" class="topic sticker">
    <span class="hd">
      <span class="ti" :style="{ background: hue }"><Icon :name="icon || 'grid'" :size="18" /></span>
      <span class="txt">
        <span class="name">{{ name }}</span>
        <span class="line" :class="chips?.[0]?.tone">{{ chips?.[0]?.text ?? sub }}</span>
      </span>
    </span>
    <span v-if="chips && chips.length > 1" class="chips">
      <span v-for="c in chips.slice(1)" :key="c.text" class="pill" :class="c.tone">{{ c.text }}</span>
    </span>
    <span v-if="more?.length" class="more">
      <span v-for="(m, i) in more" :key="i" class="row"><span class="rt" :class="m.tone">{{ '♡ ' }}{{ m.text }}</span><span v-if="m.sub" class="rs">{{ m.sub }}</span></span>
    </span>
    <span class="peel" aria-hidden="true" />
  </NuxtLink>
</template>

<style scoped>
.sticker {
  position: relative; display: flex; flex-direction: column; gap: 8px; height: 100%; min-width: 0; overflow: hidden; padding: 12px 14px;
  color: var(--text); text-decoration: none; border-radius: 20px; background: var(--panel); border: 4px solid var(--panel);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent) 14%, var(--line)), 0 6px 14px rgba(214, 69, 140, .12);
}
.sticker:hover { text-decoration: none; animation: kwwiggle .5s ease-in-out; }
.sticker:active { transform: scale(.97); }
.hd { display: flex; align-items: center; gap: 10px; min-width: 0; }
.ti { flex: none; display: grid; place-items: center; width: 36px; height: 36px; border-radius: 50%; color: var(--text); }
.txt { display: flex; flex-direction: column; min-width: 0; }
.name { font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.line { font-size: 12px; font-weight: 700; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.line.ok { color: var(--ok); } .line.warn { color: var(--warn); } .line.bad { color: var(--bad); }
.chips { display: flex; gap: 4px; flex-wrap: wrap; max-height: 50px; overflow: hidden; }
.more { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; border-top: 2px dotted var(--line); padding-top: 4px; }
.row { display: flex; gap: 10px; padding: 2px 0; font-size: 12.5px; min-width: 0; }
.rt { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rt.ok { color: var(--ok); } .rt.warn { color: var(--warn); } .rt.bad { color: var(--bad); }
.rs { margin-left: auto; flex: none; color: var(--faint); font-size: 12px; }
.peel { position: absolute; right: -4px; bottom: -4px; width: 22px; height: 22px; border-top-left-radius: 10px; background: linear-gradient(135deg, color-mix(in srgb, var(--accent) 18%, var(--panel-2)) 50%, transparent 50%); box-shadow: -2px -2px 4px rgba(122, 84, 105, .12); }
@keyframes kwwiggle { 25% { transform: rotate(-1.5deg); } 50% { transform: rotate(1.2deg); } 75% { transform: rotate(-.6deg); } }
@container tile (max-width: 129px) {
  .sticker { align-items: center; justify-content: center; text-align: center; padding: 8px 6px; }
  .hd { flex-direction: column; gap: 6px; }
  .name { font-size: 12px; }
  .line, .chips, .more { display: none; }
}
@container tile (max-height: 99px) { .chips, .more { display: none; } .sticker { justify-content: center; } }
@media (prefers-reduced-motion: reduce) { .sticker:hover { animation: none; } }
</style>
