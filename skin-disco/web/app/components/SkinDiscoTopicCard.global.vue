<script setup lang="ts">
/** Home tile as a record sleeve: a coloured sleeve with the name, a vinyl single sliding out of its top corner (it spins and slides further out on hover/press) */
const props = withDefaults(defineProps<{
  to?: string, icon?: string, name?: string, sub?: string, chips?: { text: string, tone?: string }[]
  more?: { text: string, sub?: string, tone?: string }[]
}>(), { to: '/', icon: 'grid', name: '' })
const SLEEVES = [
  'linear-gradient(135deg, rgba(255, 63, 180, .32), rgba(180, 75, 255, .14))',
  'linear-gradient(135deg, rgba(63, 216, 255, .28), rgba(180, 75, 255, .14))',
  'linear-gradient(135deg, rgba(255, 201, 63, .26), rgba(255, 63, 180, .14))',
  'linear-gradient(135deg, rgba(63, 242, 160, .24), rgba(63, 216, 255, .12))',
]
const LABELS = ['var(--accent)', 'rgba(63, 216, 255, 1)', 'var(--warn)', 'var(--ok)']
const h = computed(() => { let x = 0; for (const c of props.to ?? props.name ?? '') x = (x * 31 + c.charCodeAt(0)) >>> 0; return x })
const head = computed(() => props.chips?.[0] ?? (props.sub ? { text: props.sub, tone: '' } : null))
</script>

<template>
  <NuxtLink :to="to" class="topic dsleeve" :style="{ '--sleeve': SLEEVES[h % 4], '--lbl': LABELS[h % 4] }">
    <span class="vinyl" aria-hidden="true"><i /></span>
    <span class="hd">
      <span class="ic"><Icon :name="icon" :size="16" /></span>
      <span class="nm">{{ name }}</span>
    </span>
    <span v-if="head" class="say" :class="head.tone">{{ head.text }}</span>
    <span v-if="chips && chips.length > 1" class="chips">
      <span v-for="c in chips.slice(1)" :key="c.text" class="pill" :class="c.tone">{{ c.text }}</span>
    </span>
    <span v-if="more?.length" class="more">
      <span v-for="(r, i) in more" :key="i" class="row"><span class="rt" :class="r.tone">{{ r.text }}</span><span v-if="r.sub" class="rs">{{ r.sub }}</span></span>
    </span>
  </NuxtLink>
</template>

<style scoped>
.dsleeve {
  position: relative; display: flex; flex-direction: column; gap: 7px; height: 100%; min-width: 0; overflow: hidden; padding: 10px 12px;
  color: var(--text); text-decoration: none; border-radius: var(--radius, 14px);
  background: var(--sleeve), var(--panel); border: 1.5px solid var(--line-2);
  box-shadow: 0 6px 18px rgba(0, 0, 0, .35); transition: transform .2s, box-shadow .2s;
}
.dsleeve:hover { text-decoration: none; transform: translateY(-2px); box-shadow: 0 0 18px rgba(255, 63, 180, .35); }
.dsleeve:active { transform: scale(.98); }
.vinyl {
  position: absolute; right: -30px; top: -30px; width: 76px; height: 76px; border-radius: 50%; pointer-events: none; opacity: .9;
  background: repeating-radial-gradient(circle, rgba(16, 10, 24, 1) 0 1.5px, rgba(44, 36, 58, 1) 2px 2.6px);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, .12); transition: transform .45s cubic-bezier(.3, 1.4, .5, 1);
}
.vinyl i { position: absolute; inset: 34%; border-radius: 50%; background: var(--lbl); }
.vinyl i::after { content: ''; position: absolute; inset: 40%; border-radius: 50%; background: rgba(10, 4, 20, 1); }
.dsleeve:hover .vinyl, .dsleeve:active .vinyl { transform: translate(-8px, 8px) rotate(200deg); }
.hd { position: relative; display: flex; align-items: center; gap: 8px; min-width: 0; padding-right: 34px; }
.ic { flex: none; display: grid; place-items: center; width: 28px; height: 28px; border-radius: 50%; color: var(--text); background: rgba(10, 4, 20, .6); box-shadow: 0 0 0 1.5px var(--lbl), 0 0 10px var(--lbl); }
.nm { min-width: 0; font-size: 14.5px; font-weight: 900; font-style: italic; letter-spacing: .02em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.say { position: relative; font-size: 13px; font-weight: 700; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.say.ok, .rt.ok { color: var(--ok); } .say.warn, .rt.warn { color: var(--warn); } .say.bad, .rt.bad { color: var(--bad); }
.chips { display: flex; flex-wrap: wrap; gap: 4px; }
.more { display: none; flex-direction: column; min-height: 0; overflow: hidden; }
.row { display: flex; gap: 8px; align-items: baseline; padding: 2px 0; font-size: 12.5px; min-width: 0; border-bottom: 1px dashed color-mix(in srgb, var(--line-2) 60%, transparent); }
.rt { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rs { margin-left: auto; flex: none; font-size: 11.5px; color: var(--faint); }
@container tile (max-height: 99px) { .chips { display: none; } .dsleeve { padding: 7px 10px; } }
@container tile (min-height: 100px) { .more { display: flex; } }
@container tile (max-width: 129px) {
  .dsleeve { align-items: center; padding: 8px 5px; gap: 4px; }
  .hd { flex-direction: column; gap: 3px; padding-right: 0; }
  .nm { font-size: 11px; max-width: 100%; text-align: center; }
  .say { font-size: 11px; max-width: 100%; }
  .chips, .more { display: none; }
}
@media (prefers-reduced-motion: reduce) { .dsleeve, .vinyl { transition: none; } }
</style>
