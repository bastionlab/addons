<script setup lang="ts">
/**
 * Modal for the calendar: a centred sheet on desktop, a bottom sheet on phones (slides up, transform + opacity only).
 * Escape and a click on the backdrop are reported (the owner decides whether they close); Tab stays inside;
 * focus goes to [data-autofocus] (else the first field) and back to where it was on close.
 */
const props = defineProps<{ open: boolean, label: string, full?: boolean }>()
const emit = defineEmits<{ esc: [], backdrop: [] }>()
const el = ref<HTMLElement>()
let prev: HTMLElement | null = null

const FOCUSABLE = 'button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), a[href], [tabindex]:not([tabindex="-1"])'
const items = () => [...(el.value?.querySelectorAll<HTMLElement>(FOCUSABLE) ?? [])].filter(x => x.offsetParent !== null)

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') { e.preventDefault(); emit('esc'); return }
  if (e.key !== 'Tab') return
  const f = items()
  if (!f.length) return
  const first = f[0] as HTMLElement, last = f[f.length - 1] as HTMLElement
  if (e.shiftKey && (document.activeElement === first || !el.value?.contains(document.activeElement))) { e.preventDefault(); last.focus() }
  else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
}

watch(() => props.open, async (o) => {
  document.documentElement.style.overflow = o ? 'hidden' : ''
  if (o) {
    prev = document.activeElement as HTMLElement | null
    window.addEventListener('keydown', onKey)
    await nextTick()
    ;(el.value?.querySelector<HTMLElement>('[data-autofocus]') ?? items()[0])?.focus()
  } else {
    window.removeEventListener('keydown', onKey)
    prev?.focus?.(); prev = null
  }
}, { immediate: true })
onUnmounted(() => { window.removeEventListener('keydown', onKey); if (props.open) document.documentElement.style.overflow = '' })
</script>

<template>
  <Teleport to="body">
    <Transition name="cs" :duration="160">
      <div v-if="open" class="cs-ov" @pointerdown.self="emit('backdrop')">
        <div ref="el" class="cs" :class="{ full }" role="dialog" aria-modal="true" :aria-label="label">
          <div v-if="$slots.header" class="cs-head"><slot name="header" /></div>
          <div class="cs-body"><slot /></div>
          <div v-if="$slots.footer" class="cs-foot"><slot name="footer" /></div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.cs-ov { position: fixed; inset: 0; z-index: 75; background: rgb(0 0 0 / .5); display: flex; align-items: center; justify-content: center; padding: 16px; }
.cs { width: min(520px, 100%); max-height: min(760px, 100%); display: flex; flex-direction: column; background: var(--panel); border: 1px solid var(--line-2); border-radius: var(--radius); box-shadow: 0 24px 64px rgb(0 0 0 / .45); overflow: hidden; }
.cs-body { flex: 1; min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding: 18px 18px 8px; }
.cs-foot { padding: 12px 18px; border-top: 1px solid var(--line); }
.cs-head { display: none; }

.cs-enter-active, .cs-leave-active { transition: opacity .16s ease; }
.cs-enter-active .cs, .cs-leave-active .cs { transition: transform .16s ease, opacity .16s ease; }
.cs-enter-from, .cs-leave-to { opacity: 0; }
.cs-enter-from .cs, .cs-leave-to .cs { opacity: 0; transform: translateY(8px); }

@media (max-width: 640px) {
  .cs-ov { align-items: flex-end; padding: 0; }
  .cs { width: 100%; max-height: 92dvh; border-radius: 16px 16px 0 0; border-bottom: 0; }
  .cs-body { padding: 16px 14px 6px; }
  .cs-foot { padding: 10px 14px calc(10px + env(safe-area-inset-bottom, 0px)); }
  /* full: the editor takes the whole screen; its header stays put while the fields scroll */
  .cs.full { height: 100dvh; max-height: none; border-radius: 0; border: 0; }
  .cs-head { display: grid; grid-template-columns: minmax(64px, auto) minmax(0, 1fr) minmax(64px, auto); align-items: center; gap: 8px; flex: none; min-height: 52px; padding: env(safe-area-inset-top, 0px) 8px 0; border-bottom: 1px solid var(--line); background: var(--panel); }
  .cs.full .cs-head ~ .cs-body { padding-top: 14px; }
  .cs-enter-from .cs, .cs-leave-to .cs { opacity: 1; transform: translateY(100%); }
}
@media (prefers-reduced-motion: reduce) {
  .cs-enter-active, .cs-leave-active, .cs-enter-active .cs, .cs-leave-active .cs { transition: none; }
}
</style>
