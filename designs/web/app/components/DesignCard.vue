<script setup lang="ts">
/** one design: a small live preview painted with its own tokens, its name, and the buttons the page passes in */
const props = defineProps<{ name: string, tokens: DesignTokens, sub?: string, active?: boolean }>()
const vars = computed(() => {
  const t = props.tokens, v: Record<string, string> = {}
  for (const k of DESIGN_COLORS) if (t[k]) v[`--d-${k}`] = t[k]
  v['--d-radius'] = `${t.radius ?? 12}px`
  return v
})
</script>

<template>
  <div class="dcard" :class="{ active }">
    <div class="prev" :style="vars">
      <div class="pp">
        <span class="bar" />
        <span class="bar short" />
        <span class="dots"><i class="a" /><i class="o" /><i class="w" /><i class="b" /></span>
      </div>
    </div>
    <div class="meta">
      <div class="nm">
        {{ name }} <span v-if="active" class="pill accent">{{ $t('designs.inUse') }}</span>
      </div>
      <div v-if="sub" class="faint small">{{ sub }}</div>
    </div>
    <div class="acts"><slot /></div>
  </div>
</template>

<style scoped>
.dcard { display: flex; flex-direction: column; gap: 8px; padding: 10px; border: 1px solid var(--line); border-radius: var(--radius); background: var(--panel-2); }
.dcard.active { border-color: var(--accent); }
.prev { background: var(--d-bg); border-radius: var(--d-radius); padding: 10px; border: 1px solid var(--d-line); }
.pp { background: var(--d-panel); border: 1px solid var(--d-line-2); border-radius: var(--d-radius); padding: 8px; display: flex; flex-direction: column; gap: 6px; }
.bar { height: 6px; border-radius: 3px; background: var(--d-text); width: 70%; opacity: .9; }
.bar.short { width: 45%; background: var(--d-muted); }
.dots { display: flex; gap: 5px; }
.dots i { width: 14px; height: 14px; border-radius: 50%; }
.dots .a { background: var(--d-accent); } .dots .o { background: var(--d-ok); } .dots .w { background: var(--d-warn); } .dots .b { background: var(--d-bad); }
.nm { font-weight: 600; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.acts { display: flex; gap: 6px; flex-wrap: wrap; margin-top: auto; }
</style>
