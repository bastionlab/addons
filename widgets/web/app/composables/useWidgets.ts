import { MAX_WIDGETS, type WidgetDef } from '../utils/widgets'

/**
 * The owner's widgets: definitions (widgets:defs) and which of them sit on Home on this kind of device
 * (widgets:place:<phone|tablet|desktop>), both synced across devices (useSynced). Call it once, in HomeWidgets.
 */
export function useWidgets() {
  const defs = useSynced<WidgetDef[]>('widgets:defs', () => [])
  const place = useSynced<string[]>(`widgets:place:${deviceKind()}`, () => [])
  const list = computed(() => (Array.isArray(defs.value.value) ? defs.value.value : []) as WidgetDef[])
  const placed = computed(() => (Array.isArray(place.value.value) ? place.value.value : []) as string[])
  const onHome = computed(() => placed.value.map(id => list.value.find(d => d.id === id)).filter((d): d is WidgetDef => !!d))
  const has = (id: string) => placed.value.includes(id)

  /** add or replace a definition (already cleaned by cleanWidget) */
  function save(d: WidgetDef, home = true) {
    if (!list.value.some(x => x.id === d.id) && list.value.length >= MAX_WIDGETS) throw new Error('limit')
    defs.set([...list.value.filter(x => x.id !== d.id), d])
    if (home && !has(d.id)) place.set([...placed.value, d.id])
  }
  function remove(id: string) {
    defs.set(list.value.filter(x => x.id !== id))
    place.set(placed.value.filter(x => x !== id))
  }
  function toggle(id: string) { place.set(has(id) ? placed.value.filter(x => x !== id) : [...placed.value, id]) }
  function move(id: string, by: -1 | 1) {
    const a = [...placed.value], i = a.indexOf(id), j = i + by
    if (i < 0 || j < 0 || j >= a.length) return
    ;[a[i], a[j]] = [a[j]!, a[i]!]
    place.set(a)
  }
  return { list, placed, onHome, has, save, remove, toggle, move }
}
export type WidgetsApi = ReturnType<typeof useWidgets>
