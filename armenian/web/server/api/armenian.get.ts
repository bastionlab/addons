/** progress + the card to study next: the queue is decided here so every device studies the same one */
export default defineEventHandler(() => ({ ...armenianOverview(), next: armNextCard() }))
