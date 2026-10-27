/** Habits effects: confetti, the ding that climbs the scale and the perfect-day fanfare (all skipped for reduced motion) */
const reduced = () => typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches
const SOUND_KEY = 'habits:sound'
export const soundOn = () => { try { return localStorage.getItem(SOUND_KEY) !== 'off' } catch { return true } }
export const setSoundOn = (on: boolean) => { try { localStorage.setItem(SOUND_KEY, on ? 'on' : 'off') } catch {} }

function palette() {
  const s = getComputedStyle(document.documentElement)
  return ['--ok', '--accent', '--warn', '--bad', '--text', '--claude'].map(v => s.getPropertyValue(v).trim()).filter(Boolean)
}

/** confetti from the middle of `el` */
export function burst(el: Element | null | undefined, n: number, spread: number) {
  if (!el || reduced()) return
  const colors = palette(), r = el.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2
  for (let i = 0; i < n; i++) {
    const b = document.createElement('i')
    b.className = 'hb-bit' + (i % 3 ? '' : ' round')
    b.style.cssText = `position:fixed;z-index:200;pointer-events:none;width:${i % 3 ? 6 : 7}px;height:${i % 3 ? 10 : 7}px;border-radius:${i % 3 ? 2 : 50}%;left:${x}px;top:${y}px;background:${colors[i % colors.length]}`
    document.body.append(b)
    const a = Math.random() * Math.PI * 2, d = spread * (.45 + Math.random() * .75)
    const dx = Math.cos(a) * d, dy = Math.sin(a) * d
    b.animate([
      { transform: 'translate(-50%, -50%) scale(0)', opacity: 1 },
      { transform: `translate(calc(-50% + ${dx * .7}px), calc(-50% + ${dy * .7}px)) rotate(${Math.random() * 360}deg) scale(1)`, opacity: 1, offset: .35 },
      { transform: `translate(calc(-50% + ${dx}px), calc(-50% + ${dy + spread * .5}px)) rotate(${Math.random() * 720}deg) scale(.5)`, opacity: 0 },
    ], { duration: 700 + Math.random() * 500, easing: 'cubic-bezier(.1, .7, .3, 1)' }).onfinish = () => b.remove()
  }
}

/** confetti falling from the top of the screen */
export function rain(n: number) {
  if (reduced()) return
  const colors = palette()
  for (let i = 0; i < n; i++) {
    const b = document.createElement('i')
    b.style.cssText = `position:fixed;z-index:200;pointer-events:none;width:${i % 3 ? 6 : 7}px;height:${i % 3 ? 10 : 7}px;border-radius:${i % 3 ? 2 : 50}%;left:${Math.random() * innerWidth}px;top:-12px;background:${colors[i % colors.length]}`
    document.body.append(b)
    const drift = (Math.random() - .5) * 160
    b.animate([
      { transform: 'translateY(0) rotate(0)', opacity: 1 },
      { transform: `translate(${drift}px, ${innerHeight + 40}px) rotate(${(Math.random() - .5) * 1440}deg)`, opacity: .9 },
    ], { duration: 1800 + Math.random() * 1600, delay: Math.random() * 900, easing: 'cubic-bezier(.25, .5, .5, 1)', fill: 'backwards' }).onfinish = () => b.remove()
  }
}

/** "+10 XP" rising off the row you just checked */
export function floatXp(row: Element | null | undefined, text: string) {
  if (!row || reduced()) return
  const r = row.getBoundingClientRect(), b = document.createElement('b')
  b.textContent = text
  b.style.cssText = `position:fixed;z-index:200;pointer-events:none;color:var(--warn);font-weight:800;font-size:14px;left:${r.right - 70}px;top:${r.top + r.height / 2 - 10}px`
  document.body.append(b)
  b.animate([
    { transform: 'translateY(6px) scale(.6)', opacity: 0 },
    { transform: 'translateY(-10px) scale(1.15)', opacity: 1, offset: .25 },
    { transform: 'translateY(-46px) scale(1)', opacity: 0 },
  ], { duration: 1100, easing: 'cubic-bezier(.2, .8, .2, 1)' }).onfinish = () => b.remove()
}

export const vibrate = (p: number | number[]) => { if (!reduced()) navigator.vibrate?.(p) }

let actx: AudioContext | undefined
const SCALE = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19]
function note(f: number, at: number, dur: number, vol = .14, type: OscillatorType = 'triangle') {
  const c = actx!, o = c.createOscillator(), g = c.createGain(), t = c.currentTime + at
  o.type = type; o.frequency.value = f
  g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vol, t + .012); g.gain.exponentialRampToValueAtTime(.0008, t + dur)
  o.connect(g).connect(c.destination); o.start(t); o.stop(t + dur + .05)
}
/** check: a ding that climbs with every habit done today; win: the perfect-day fanfare */
export function sfx(kind: 'check' | 'win', n = 1) {
  if (!soundOn()) return
  try { actx ??= new AudioContext(); actx.resume() } catch { return }
  const f = 587.33 * 2 ** (SCALE[Math.min(n - 1, SCALE.length - 1)]! / 12)
  if (kind === 'check') { note(f, 0, .12); note(f * 1.5, .07, .28) }
  else {
    [523.25, 659.25, 783.99, 1046.5].forEach((x, i) => note(x, i * .11, .3, .13))
    for (const x of [523.25, 659.25, 783.99, 1046.5, 1318.5]) note(x, .5, 1.3, .07, 'sine')
  }
}
