// Hands-free chat loop. The chat page publishes a handle (useState 'chat:voice'); this drives it.
// States: off -> listening -> transcribing -> review (what was heard, 2 s to cancel) -> sending -> waiting (reply running)
// -> speaking -> listening ...
// Voice activity is plain energy (RMS of an AnalyserNode); the mic is only live while listening, so the
// speaker is never picked up as speech.
export interface VoiceHandle {
  send: (text: string) => void
  engineLabel: () => 'Claude' | 'local model'
  lastAnswer: () => { text: string, busy: boolean, n: number, error?: string }
  idle: () => boolean
}
export interface StartOpts { key: string, text: string, full?: boolean }
export type VoiceState = 'off' | 'listening' | 'transcribing' | 'review' | 'sending' | 'waiting' | 'speaking'

const THRESHOLD = 0.02 // RMS that counts as speech
const START_MS = 150 // above threshold this long = speech began
const END_MS = 900 // below threshold this long = speech ended
const MIN_MS = 400 // shorter segments are noise
const TICK = 50
const REVIEW_MS = 2000 // the transcript stays editable-by-cancel this long before it is sent

export function useVoiceLoop() {
  const state = useState<VoiceState>('voice:state', () => 'off')
  const heard = useState('voice:heard', () => '')
  const note = useState('voice:note', () => '')
  // not useI18n(): the loop is also started from a click handler, outside component setup
  const t = (key: string, params?: Record<string, unknown>) => (useNuxtApp().$i18n as any).t(key, params ?? {})
  const sp = useSpeak()
  const runtime = (globalThis as any).__voice ??= { gen: 0, skip: null as null | (() => void), cleanup: [] as (() => void)[], review: '' as '' | 'send' | 'cancel' }
  const handle = () => useState<VoiceHandle | null>('chat:voice').value
  const alive = (g: number) => runtime.gen === g
  const sleep = (ms: number) => new Promise(r => setTimeout(r, ms))

  // one utterance: resolves with the recorded blob, or null when aborted
  function listen(stream: MediaStream, g: number): Promise<Blob | null> {
    return new Promise((resolve) => {
      const ctx = new AudioContext()
      const an = ctx.createAnalyser()
      an.fftSize = 1024
      ctx.createMediaStreamSource(stream).connect(an)
      const buf = new Float32Array(an.fftSize)
      const mime = ['audio/webm;codecs=opus', 'audio/mp4'].find(m => MediaRecorder.isTypeSupported(m))
      let rec: MediaRecorder, chunks: Blob[] = []
      const fresh = () => { chunks = []; rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined); rec.ondataavailable = e => e.data.size && chunks.push(e.data); rec.start() }
      fresh()
      let loud = 0, quiet = 0, since = 0, talking = false
      const finish = (blob: Blob | null) => { clearInterval(iv); runtime.skip = null; ctx.close().catch(() => {}); resolve(blob) }
      runtime.skip = () => { rec.state !== 'inactive' && rec.stop(); finish(null) }
      const iv = setInterval(() => {
        if (!alive(g)) return runtime.skip?.()
        an.getFloatTimeDomainData(buf)
        const rms = Math.sqrt(buf.reduce((s, v) => s + v * v, 0) / buf.length)
        if (rms > THRESHOLD) { loud += TICK; quiet = 0 } else { quiet += TICK; if (!talking) loud = 0 }
        if (!talking && loud >= START_MS) { talking = true; since = Date.now() - loud }
        if (talking && quiet >= END_MS) {
          if (Date.now() - since - quiet < MIN_MS) { // too short: drop it and keep listening
            talking = false; loud = quiet = 0
            rec.onstop = () => fresh(); rec.stop()
            return
          }
          clearInterval(iv)
          rec.onstop = () => finish(new Blob(chunks, { type: rec.mimeType || 'audio/webm' }))
          rec.stop()
        }
      }, TICK)
    })
  }

  async function transcribe(blob: Blob) {
    const fd = new FormData()
    fd.append('audio', blob, blob.type.includes('mp4') ? 'voice.m4a' : 'voice.webm')
    const r = await $fetch<{ text: string }>('/api/chat/transcribe', { method: 'POST', body: fd })
    return (r.text || '').trim()
  }

  // read an answer aloud; a tap on the orb (sp.stop) ends it early
  async function say(g: number, key: string, text: string, full = false) {
    if (!text.trim() || !alive(g)) return
    state.value = 'speaking'
    await sp.speak(key, text, full)
  }

  async function run(g: number, first?: StartOpts) {
    let wake: any
    let stream: MediaStream | undefined
    try {
      // read first: playback has to start inside the tap, a mic permission prompt before it would make phones refuse
      let a = handle()?.lastAnswer()
      if (first) await say(g, first.key, first.text, first.full)
      else if (a && !a.busy && !a.error) await say(g, `voice:${a.n}`, a.text)
      if (!alive(g)) return
      stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } })
      try { wake = await (navigator as any).wakeLock?.request('screen') } catch {}
      while (alive(g)) {
        const h = handle()
        if (!h) break
        state.value = 'listening'
        const blob = await listen(stream, g)
        if (!blob || !alive(g)) continue
        state.value = 'transcribing'
        let text = ''
        try { text = await transcribe(blob) } catch (e: any) {
          note.value = t('voice.failed', { msg: e?.data?.statusMessage || e?.message || 'error' })
          await sleep(2000); note.value = ''
          continue
        }
        if (!text || !alive(g)) continue
        heard.value = text
        if (!h.idle()) continue // never send into a running reply
        // show what was heard and give a moment to cancel (Whisper only answers after the pause, so no live text)
        state.value = 'review'; runtime.review = ''
        for (let w = 0; w < REVIEW_MS && alive(g) && !runtime.review; w += 100) await sleep(100)
        const cancelled = runtime.review === 'cancel'
        runtime.review = ''
        if (cancelled) { heard.value = ''; continue }
        if (!alive(g)) break
        state.value = 'sending'
        note.value = h.engineLabel() === 'Claude' ? t('voice.toClaude') : t('voice.toLocal')
        h.send(text)
        await sleep(600)
        note.value = ''
        state.value = 'waiting'
        // the reply is done when the chat has no running turn any more
        while (alive(g) && (handle()?.lastAnswer().busy || !handle()?.idle())) await sleep(300)
        a = handle()?.lastAnswer()
        if (alive(g) && a && !a.error) await say(g, `voice:${a.n}`, a.text)
      }
    } catch (e: any) {
      note.value = t('voice.failed', { msg: e?.message || 'microphone' })
      await sleep(2500)
    } finally {
      stream?.getTracks().forEach(x => x.stop())
      wake?.release?.().catch?.(() => {})
      if (alive(g)) { state.value = 'off'; note.value = '' }
    }
  }

  // started by the read-aloud button of an answer (first = that answer), or without it: reads the newest answer
  function start(first?: StartOpts) {
    if (state.value !== 'off' || !handle()) return
    heard.value = ''; note.value = ''
    run(++runtime.gen, first)
  }
  const sendNow = () => { runtime.review = 'send' }
  const cancel = () => { runtime.review = 'cancel' }
  function stop() {
    runtime.gen++
    sp.stop()
    runtime.skip?.()
    state.value = 'off'
    note.value = ''
  }
  // tap on the orb: while speaking skip to listening, otherwise just stop talking over it
  function interrupt() {
    if (state.value === 'speaking') sp.stop()
    else if (state.value === 'listening') stop()
  }
  return { state, heard, note, start, stop, interrupt, sendNow, cancel, review: computed(() => state.value === 'review'), on: computed(() => state.value !== 'off') }
}
