/** keep asking the agent to sort what is still pending (12 per call) until nothing is left, a call sorts nothing
 *  (model unavailable) or `max` rounds are used; `onLeft(left, done)` drives a progress count */
export async function drainTriage(account: string, max: number, onLeft?: (left: number, done: number) => void) {
  let done = 0, left = 0, note = ''
  for (let i = 0; i < max; i++) {
    const r = await $fetch<any>('/api/mail/triage', { method: 'POST', body: { account } })
    done += r.triaged || 0; left = r.pending || 0; note = r.note || ''
    onLeft?.(left, done)
    if (!left || !r.triaged) break
  }
  return { done, left, note }
}
