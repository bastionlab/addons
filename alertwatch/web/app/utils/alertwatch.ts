/** alerts.py writes Discord markdown (**bold**, `code`): plain text for a one-line row */
export const alertPlain = (m: unknown) => String(m ?? '').replace(/[*`]/g, '').replace(/\s+/g, ' ').trim()

/**
 * "Execute fix": hands the plan turn to the chat page through sessionStorage, not a URL parameter, so a link from
 * outside can never start a write turn (chat.vue reads and removes `bastion:exec`, < 60 s old).
 */
export function alertwatchExecute(chat: string, turn: string) {
  sessionStorage.setItem('bastion:exec', JSON.stringify({ chat, turn, at: Date.now() }))
  return navigateTo('/chat?c=' + chat)
}
