/**
 * Scoring for the Armenian trace pad. Pure (masks in, numbers out) so it can be tested without a canvas.
 * glyph / ink = w*h masks (1 = painted). coverage = share of glyph pixels with ink within `near` px; spill = share of
 * ink pixels farther than `far` px from any glyph pixel; fat = ink area / glyph area (a scribble floods the glyph).
 */
export interface TraceScore { cov: number, spill: number, fat: number, pass: boolean }

/** grow a mask by r px in every direction (square window, two sliding passes) */
export function dilate(m: Uint8Array, w: number, h: number, r: number): Uint8Array {
  const tmp = new Uint8Array(w * h), out = new Uint8Array(w * h)
  const pre = new Int32Array(Math.max(w, h) + 1)
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) pre[x + 1] = pre[x]! + (m[y * w + x] ? 1 : 0)
    for (let x = 0; x < w; x++) tmp[y * w + x] = pre[Math.min(w, x + r + 1)]! - pre[Math.max(0, x - r)]! > 0 ? 1 : 0
  }
  for (let x = 0; x < w; x++) {
    for (let y = 0; y < h; y++) pre[y + 1] = pre[y]! + tmp[y * w + x]!
    for (let y = 0; y < h; y++) out[y * w + x] = pre[Math.min(h, y + r + 1)]! - pre[Math.max(0, y - r)]! > 0 ? 1 : 0
  }
  return out
}

export function traceScore(glyph: Uint8Array, ink: Uint8Array, w: number, h: number, near = 14, far = 24): TraceScore {
  let g = 0, k = 0
  for (let i = 0; i < glyph.length; i++) { if (glyph[i]) g++; if (ink[i]) k++ }
  if (!g || !k) return { cov: 0, spill: k ? 1 : 0, fat: 0, pass: false }
  const inkNear = dilate(ink, w, h, near), glyphFar = dilate(glyph, w, h, far)
  let covered = 0, spilled = 0
  for (let i = 0; i < glyph.length; i++) {
    if (glyph[i] && inkNear[i]) covered++
    if (ink[i] && !glyphFar[i]) spilled++
  }
  const cov = covered / g, spill = spilled / k, fat = k / g
  return { cov, spill, fat, pass: cov >= 0.5 && spill <= 0.5 && fat <= 3 }
}
