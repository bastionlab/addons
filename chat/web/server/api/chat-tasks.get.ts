/** the chat's scheduled tasks (owner only: not in CORE_API) */
export default defineEventHandler(() => ({ tasks: loadTasks().sort((a, b) => (a.next ?? 0) - (b.next ?? 0)) }))
