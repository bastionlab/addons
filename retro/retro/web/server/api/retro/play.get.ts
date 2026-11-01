/**
 * The player: a bare page around EmulatorJS (its cores come from the EmulatorJS CDN, pinned below), so it gets the
 * whole screen and the touch gamepad on a phone. Saves go to the host instead of this browser:
 * - the game's own save (srm) is fetched when the game starts and sent back every 15 s and when you leave
 * - the menu's Save state / Load state buttons write / read the host's copy
 */
const EJS = 'https://cdn.emulatorjs.org/4.2.3/data/'
const CORES: Record<string, string> = {
  nes: 'nes', snes: 'snes', n64: 'n64', gb: 'gb', gbc: 'gbc', gba: 'gba', nds: 'nds', vb: 'vb', sms: 'segaMS',
  gg: 'segaGG', md: 'segaMD', segacd: 'segaCD', '32x': 'sega32x', saturn: 'segaSaturn', psx: 'psx', psp: 'psp',
  pce: 'pce', ngp: 'ngp', ws: 'ws', lynx: 'lynx', a2600: 'atari2600', a7800: 'atari7800', arcade: 'arcade',
}

export default defineEventHandler(async (event) => {
  const q = getQuery(event)
  const sys = String(q.sys ?? ''), name = String(q.name ?? '')
  const core = CORES[sys]
  if (!core || !name || name.includes('/')) throw createError({ statusCode: 400, statusMessage: 'bad game' })
  const lib: any = await agent(event, '/retro')
  if (!lib.games.some((g: any) => g.sys === sys && g.file === name)) throw createError({ statusCode: 404, statusMessage: 'no such game' })
  const bios = lib.bios.includes(sys)
  const threads = sys === 'psp'
  // PSP's core needs threads = SharedArrayBuffer = a cross-origin-isolated page (the CDN sends CORP, so it still loads)
  if (threads) setResponseHeaders(event, { 'Cross-Origin-Opener-Policy': 'same-origin', 'Cross-Origin-Embedder-Policy': 'require-corp' })
  setResponseHeaders(event, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' })
  const cfg = { sys, name, core, bios, threads, title: name.replace(/\.[^.]+$/, '') }
  const json = JSON.stringify(cfg).replace(/</g, '\\u003c')
  return `<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<meta name="theme-color" content="black"><title>${cfg.title.replace(/[<&"]/g, '')} · Bastion</title>
<style>
html,body{margin:0;height:100%;background:black;overflow:hidden;overscroll-behavior:none}
#game{width:100vw;height:100dvh}
#back{position:fixed;top:max(8px,env(safe-area-inset-top));left:8px;z-index:9999;font:600 14px system-ui,sans-serif;color:white;
  background:rgba(0,0,0,.45);border:1px solid rgba(255,255,255,.2);border-radius:999px;padding:4px 10px;text-decoration:none;opacity:.75}
#sync{position:fixed;top:max(8px,env(safe-area-inset-top));right:8px;z-index:9999;font:12px system-ui,sans-serif;color:rgba(255,255,255,.7);
  background:rgba(0,0,0,.45);border-radius:999px;padding:4px 10px;display:none}
</style></head><body>
<a id="back" href="/retro">‹ Library</a><div id="sync"></div><div id="game"></div>
<script>
const C = ${json}
const base = '/api/retro/file?sys=' + encodeURIComponent(C.sys) + '&name=' + encodeURIComponent(C.name)
const pill = document.getElementById('sync')
let pillT
function note(t) { pill.textContent = t; pill.style.display = 'block'; clearTimeout(pillT); pillT = setTimeout(() => pill.style.display = 'none', 2500) }
document.getElementById('back').onclick = (e) => { sync(); if (history.length > 1 && document.referrer.includes('/retro')) { e.preventDefault(); history.back() } }

async function put(kind, bytes) {
  const r = await fetch('/api/retro/save?sys=' + encodeURIComponent(C.sys) + '&name=' + encodeURIComponent(C.name) + '&kind=' + kind,
    { method: 'POST', body: bytes, headers: { 'Content-Type': 'application/octet-stream' }, keepalive: bytes.length < 60000 })
  if (!r.ok) throw new Error(await r.text())
}
async function digest(d) { return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-1', d))).join(',') }

let last = null, started = false
async function sync() {
  if (!started) return
  try {
    const d = EJS_emulator.gameManager.getSaveFile()
    if (!d || !d.length) return
    const k = await digest(d)
    if (k === last) return
    await put('srm', d); last = k; note('Saved')
  } catch (e) { note('Save not synced') }
}

window.EJS_player = '#game'
window.EJS_core = C.core
window.EJS_gameUrl = base + '&kind=rom'
window.EJS_gameName = C.title
window.EJS_pathtodata = '${EJS}'
window.EJS_startOnLoaded = true
window.EJS_threads = C.threads
window.EJS_disableAutoLang = true
if (C.bios) window.EJS_biosUrl = '/api/retro/file?sys=' + encodeURIComponent(C.sys) + '&kind=bios'
window.EJS_onSaveState = async (e) => {
  try { await put('state', e.state); EJS_emulator.displayMessage('STATE SAVED (all devices)') } catch { EJS_emulator.displayMessage('SAVE FAILED') }
}
window.EJS_onLoadState = async () => {
  const r = await fetch(base + '&kind=state')
  if (!r.ok) return EJS_emulator.displayMessage('NO SAVED STATE YET')
  EJS_emulator.gameManager.loadState(new Uint8Array(await r.arrayBuffer()))
  EJS_emulator.displayMessage('STATE LOADED')
}
window.EJS_onGameStart = async () => {
  const gm = EJS_emulator.gameManager
  try {
    const r = await fetch(base + '&kind=srm')
    if (r.ok) {
      const d = new Uint8Array(await r.arrayBuffer())
      const path = gm.getSaveFilePath()
      let cp = ''
      for (const p of path.split('/').slice(0, -1)) { if (!p) continue; cp += '/' + p; if (!gm.FS.analyzePath(cp).exists) gm.FS.mkdir(cp) }
      if (gm.FS.analyzePath(path).exists) gm.FS.unlink(path)
      gm.FS.writeFile(path, d)
      gm.loadSaveFiles()
      last = await digest(d)
      note('Save loaded')
    }
  } catch (e) { note('Could not load the save') }
  started = true
  setInterval(sync, 15000)
}
document.addEventListener('visibilitychange', () => { if (document.hidden) sync() })
window.addEventListener('pagehide', sync)
</script>
<script src="${EJS}loader.js"></script>
</body></html>`
})
