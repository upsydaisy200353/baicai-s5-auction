import { isSoundMuted } from '../stores/sound'

export type SoundId =
  | 'ceremonyStart'
  | 'enterCeremony'
  | 'drawTick'
  | 'drawReveal'
  | 'bidPlace'
  | 'bidOutbid'
  | 'bidBuyout'
  | 'bidPass'
  | 'firstBid'
  | 'timerTick'
  | 'timerReset'
  | 'hammerSold'
  | 'hammerUnsold'
  | 'ceremonyEnd'
  | 'uiConfirm'
  | 'uiError'
  | 'uiClick'
  | 'poolSelect'

let audioCtx: AudioContext | null = null
const playedBidIds = new Set<number>()

function getCtx(): AudioContext {
  if (!audioCtx) audioCtx = new AudioContext()
  return audioCtx
}

export async function unlockAudio() {
  const ctx = getCtx()
  if (ctx.state === 'suspended') await ctx.resume()
}

function now(ctx: AudioContext) {
  return ctx.currentTime
}

function tone(
  ctx: AudioContext,
  freq: number,
  start: number,
  duration: number,
  opts: {
    type?: OscillatorType
    gain?: number
    attack?: number
    release?: number
    detune?: number
  } = {},
) {
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()
  const {
    type = 'sine',
    gain: peak = 0.25,
    attack = 0.008,
    release = 0.12,
    detune = 0,
  } = opts

  osc.type = type
  osc.frequency.value = freq
  osc.detune.value = detune
  gain.gain.setValueAtTime(0.0001, start)
  gain.gain.exponentialRampToValueAtTime(Math.max(peak, 0.0002), start + attack)
  gain.gain.exponentialRampToValueAtTime(0.0001, start + duration + release)
  osc.connect(gain)
  gain.connect(ctx.destination)
  osc.start(start)
  osc.stop(start + duration + release + 0.02)
}

function noiseBurst(
  ctx: AudioContext,
  start: number,
  duration: number,
  gainPeak = 0.18,
  filterFreq = 900,
) {
  const bufferSize = Math.floor(ctx.sampleRate * duration)
  const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate)
  const data = buffer.getChannelData(0)
  for (let i = 0; i < bufferSize; i++) data[i] = Math.random() * 2 - 1

  const source = ctx.createBufferSource()
  source.buffer = buffer
  const filter = ctx.createBiquadFilter()
  filter.type = 'bandpass'
  filter.frequency.value = filterFreq
  const gain = ctx.createGain()
  gain.gain.setValueAtTime(gainPeak, start)
  gain.gain.exponentialRampToValueAtTime(0.0001, start + duration)
  source.connect(filter)
  filter.connect(gain)
  gain.connect(ctx.destination)
  source.start(start)
  source.stop(start + duration + 0.02)
}

function playNotes(
  ctx: AudioContext,
  notes: Array<{ freq: number; at: number; dur: number; gain?: number; type?: OscillatorType }>,
) {
  const t0 = now(ctx)
  for (const note of notes) {
    tone(ctx, note.freq, t0 + note.at, note.dur, {
      gain: note.gain ?? 0.22,
      type: note.type ?? 'sine',
    })
  }
}

const synthesizers: Record<SoundId, (ctx: AudioContext) => void> = {
  ceremonyStart(ctx) {
    playNotes(ctx, [
      { freq: 392, at: 0, dur: 0.18, type: 'triangle' },
      { freq: 494, at: 0.12, dur: 0.18, type: 'triangle' },
      { freq: 587, at: 0.24, dur: 0.28, gain: 0.28, type: 'triangle' },
      { freq: 784, at: 0.38, dur: 0.45, gain: 0.2, type: 'sine' },
    ])
  },

  enterCeremony(ctx) {
    const t = now(ctx)
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(220, t)
    osc.frequency.exponentialRampToValueAtTime(660, t + 0.35)
    gain.gain.setValueAtTime(0.0001, t)
    gain.gain.exponentialRampToValueAtTime(0.2, t + 0.05)
    gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.45)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start(t)
    osc.stop(t + 0.5)
  },

  drawTick(ctx) {
    noiseBurst(ctx, now(ctx), 0.03, 0.12, 1400)
  },

  drawReveal(ctx) {
    playNotes(ctx, [
      { freq: 880, at: 0, dur: 0.12, gain: 0.24 },
      { freq: 1175, at: 0.08, dur: 0.16, gain: 0.26 },
      { freq: 1568, at: 0.16, dur: 0.35, gain: 0.22, type: 'triangle' },
    ])
  },

  bidPlace(ctx) {
    tone(ctx, 1046, now(ctx), 0.08, { gain: 0.2, type: 'triangle', release: 0.08 })
  },

  bidOutbid(ctx) {
    playNotes(ctx, [
      { freq: 622, at: 0, dur: 0.1, gain: 0.18, type: 'square' },
      { freq: 466, at: 0.08, dur: 0.14, gain: 0.16, type: 'triangle' },
    ])
  },

  bidBuyout(ctx) {
    const t = now(ctx)
    noiseBurst(ctx, t, 0.08, 0.22, 500)
    playNotes(ctx, [
      { freq: 523, at: 0.06, dur: 0.12, gain: 0.24, type: 'square' },
      { freq: 784, at: 0.12, dur: 0.2, gain: 0.26 },
      { freq: 1046, at: 0.2, dur: 0.35, gain: 0.22, type: 'triangle' },
    ])
  },

  bidPass(ctx) {
    playNotes(ctx, [
      { freq: 440, at: 0, dur: 0.1, gain: 0.14, type: 'triangle' },
      { freq: 330, at: 0.1, dur: 0.16, gain: 0.12, type: 'triangle' },
    ])
  },

  firstBid(ctx) {
    playNotes(ctx, [
      { freq: 659, at: 0, dur: 0.1, gain: 0.2 },
      { freq: 831, at: 0.1, dur: 0.22, gain: 0.24, type: 'triangle' },
    ])
  },

  timerTick(ctx) {
    tone(ctx, 1200, now(ctx), 0.04, { gain: 0.14, type: 'square', release: 0.04 })
  },

  timerReset(ctx) {
    const t = now(ctx)
    tone(ctx, 330, t, 0.12, { gain: 0.12, type: 'sine' })
    tone(ctx, 660, t + 0.08, 0.16, { gain: 0.16, type: 'triangle' })
  },

  hammerSold(ctx) {
    const t = now(ctx)
    for (let i = 0; i < 3; i++) {
      noiseBurst(ctx, t + i * 0.14, 0.05, 0.28 - i * 0.05, 700)
      tone(ctx, 180 - i * 20, t + i * 0.14, 0.06, { gain: 0.2, type: 'square', release: 0.05 })
    }
    playNotes(ctx, [
      { freq: 523, at: 0.42, dur: 0.15, gain: 0.2 },
      { freq: 659, at: 0.52, dur: 0.2, gain: 0.22 },
      { freq: 784, at: 0.62, dur: 0.35, gain: 0.2, type: 'triangle' },
    ])
  },

  hammerUnsold(ctx) {
    playNotes(ctx, [
      { freq: 220, at: 0, dur: 0.25, gain: 0.2, type: 'triangle' },
      { freq: 165, at: 0.2, dur: 0.35, gain: 0.18, type: 'sine' },
    ])
    noiseBurst(ctx, now(ctx) + 0.1, 0.2, 0.08, 300)
  },

  ceremonyEnd(ctx) {
    playNotes(ctx, [
      { freq: 523, at: 0, dur: 0.16, gain: 0.22, type: 'triangle' },
      { freq: 659, at: 0.14, dur: 0.16, gain: 0.22, type: 'triangle' },
      { freq: 784, at: 0.28, dur: 0.16, gain: 0.24, type: 'triangle' },
      { freq: 1046, at: 0.42, dur: 0.22, gain: 0.24 },
      { freq: 1318, at: 0.58, dur: 0.55, gain: 0.2, type: 'sine' },
    ])
  },

  uiConfirm(ctx) {
    playNotes(ctx, [
      { freq: 660, at: 0, dur: 0.08, gain: 0.16 },
      { freq: 880, at: 0.07, dur: 0.12, gain: 0.18 },
    ])
  },

  uiError(ctx) {
    playNotes(ctx, [
      { freq: 180, at: 0, dur: 0.12, gain: 0.2, type: 'square' },
      { freq: 140, at: 0.1, dur: 0.16, gain: 0.18, type: 'square' },
    ])
  },

  uiClick(ctx) {
    tone(ctx, 900, now(ctx), 0.03, { gain: 0.1, type: 'triangle', release: 0.03 })
  },

  poolSelect(ctx) {
    playNotes(ctx, [
      { freq: 494, at: 0, dur: 0.08, gain: 0.16, type: 'triangle' },
      { freq: 622, at: 0.07, dur: 0.14, gain: 0.18 },
    ])
  },
}

export function playSound(id: SoundId) {
  if (isSoundMuted()) return
  try {
    const ctx = getCtx()
    void unlockAudio()
    synthesizers[id](ctx)
  } catch {
    // ignore autoplay / audio errors
  }
}

export function markBidSoundPlayed(bidId: number) {
  playedBidIds.add(bidId)
  if (playedBidIds.size > 80) {
    const oldest = [...playedBidIds].slice(0, 40)
    oldest.forEach((id) => playedBidIds.delete(id))
  }
}

export function wasBidSoundPlayed(bidId: number) {
  return playedBidIds.has(bidId)
}

let lastHammerAt = 0

export function playHammerSold() {
  const ts = Date.now()
  if (ts - lastHammerAt < 1500) return
  lastHammerAt = ts
  playSound('hammerSold')
}
