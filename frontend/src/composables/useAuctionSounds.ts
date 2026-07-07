import { onMounted, onUnmounted, watch, type Ref } from 'vue'
import type { ServerAuctionState } from '../api/auction'
import {
  markBidSoundPlayed,
  playHammerSold,
  playSound,
  wasBidSoundPlayed,
  type SoundId,
} from '../lib/soundEngine'
import type { AuctionPhase } from '../types'

interface Options {
  selfCaptainName?: Ref<string | null | undefined>
}

interface TrackState {
  phase: AuctionPhase | null
  latestBidId: number | null
  currentLeader: string | null
  hasBids: boolean
  deadlineMs: number
  buyoutPrice: number | null
  latestBidAmount: number | null
  passedKey: string
  playerSerial: string | null
  lastResultKey: string | null
  timerSecond: number | null
  timerUrgent: boolean
}

function emptyTrack(): TrackState {
  return {
    phase: null,
    latestBidId: null,
    currentLeader: null,
    hasBids: false,
    deadlineMs: 0,
    buyoutPrice: null,
    latestBidAmount: null,
    passedKey: '',
    playerSerial: null,
    lastResultKey: null,
    timerSecond: null,
    timerUrgent: false,
  }
}

function snapshotFromState(state: ServerAuctionState): TrackState {
  const open = state.openBid
  const latest = open?.liveBids?.[0]
  const passedKey = open
    ? open.captainRows
        .filter((r) => r.passed)
        .map((r) => r.name)
        .sort()
        .join('|')
    : ''
  const deadlineMs = open?.deadlineMs ?? 0
  const secondsLeft = deadlineMs > 0 ? Math.max(0, (deadlineMs - Date.now()) / 1000) : 0
  const timerSecond = open && state.phase === 'open_bid' ? Math.floor(secondsLeft) : null

  return {
    phase: state.phase,
    latestBidId: latest?.id ?? null,
    currentLeader: open?.currentLeader ?? null,
    hasBids: open?.hasBids ?? false,
    deadlineMs,
    buyoutPrice: open?.buyoutPrice ?? null,
    latestBidAmount: latest?.amount ?? null,
    passedKey,
    playerSerial: open?.player.serial ?? state.currentPlayer?.serial ?? null,
    lastResultKey: state.lastResult
      ? `${state.lastResult.player.serial}:${state.lastResult.winner ?? 'none'}:${state.lastResult.price ?? 0}`
      : null,
    timerSecond,
    timerUrgent: secondsLeft > 0 && secondsLeft <= 8,
  }
}

function playPhaseTransition(prev: AuctionPhase | null, next: AuctionPhase, state: ServerAuctionState) {
  if (prev === next) return
  if (prev === null) return

  const phaseSounds: Partial<Record<AuctionPhase, SoundId>> = {
    intro: 'ceremonyStart',
    pool_select: 'enterCeremony',
    open_bid: 'drawReveal',
    finished: 'ceremonyEnd',
  }

  if (next === 'winner_reveal') {
    if (state.lastResult?.winner) playHammerSold()
    else playSound('hammerUnsold')
    return
  }

  const sound = phaseSounds[next]
  if (sound) playSound(sound)
}

function handleOpenBidChanges(prev: TrackState, next: TrackState, selfCaptain?: string | null) {
  if (next.phase !== 'open_bid') return

  if (prev.playerSerial !== next.playerSerial) return

  const isFirstBid = !prev.hasBids && next.hasBids
  if (isFirstBid) {
    playSound('firstBid')
  }

  if (next.latestBidId != null && next.latestBidId !== prev.latestBidId) {
    if (wasBidSoundPlayed(next.latestBidId)) return

    const isBuyout =
      next.buyoutPrice != null &&
      next.latestBidAmount != null &&
      next.latestBidAmount === next.buyoutPrice

    if (!isFirstBid) {
      if (isBuyout) {
        playSound('bidBuyout')
      } else if (prev.currentLeader && next.currentLeader && prev.currentLeader !== next.currentLeader) {
        if (selfCaptain && next.currentLeader === selfCaptain) {
          playSound('bidPlace')
        } else if (selfCaptain && prev.currentLeader === selfCaptain) {
          playSound('bidOutbid')
        } else {
          playSound('bidPlace')
        }
      } else {
        playSound('bidPlace')
      }
    }

    markBidSoundPlayed(next.latestBidId)
  }

  if (next.passedKey !== prev.passedKey && next.passedKey.length > prev.passedKey.length) {
    playSound('bidPass')
  }

  if (
    prev.deadlineMs > 0 &&
    next.deadlineMs > prev.deadlineMs + 500 &&
    next.hasBids
  ) {
    playSound('timerReset')
  }

  if (
    next.timerUrgent &&
    next.timerSecond != null &&
    next.timerSecond > 0 &&
    next.timerSecond !== prev.timerSecond
  ) {
    playSound('timerTick')
  }
}

export function useAuctionSounds(state: Ref<ServerAuctionState | null>, options: Options = {}) {
  let prev = emptyTrack()
  let initialized = false
  let timerHandle: ReturnType<typeof setInterval> | null = null

  function processState(nextState: ServerAuctionState) {
    const next = snapshotFromState(nextState)
    if (!initialized) {
      prev = next
      initialized = true
      return
    }
    playPhaseTransition(prev.phase, nextState.phase, nextState)
    handleOpenBidChanges(prev, next, options.selfCaptainName?.value ?? null)
    prev = next
  }

  function tickTimer() {
    const current = state.value
    if (!current || current.phase !== 'open_bid' || !current.openBid?.deadlineMs) return

    const secondsLeft = Math.max(0, (current.openBid.deadlineMs - Date.now()) / 1000)
    const timerSecond = Math.floor(secondsLeft)
    const timerUrgent = secondsLeft > 0 && secondsLeft <= 8

    if (timerUrgent && timerSecond > 0 && timerSecond !== prev.timerSecond) {
      playSound('timerTick')
      prev = { ...prev, timerSecond, timerUrgent }
    }
  }

  watch(
    state,
    (value) => {
      if (value) processState(value)
    },
    { deep: true },
  )

  onMounted(() => {
    if (state.value) processState(state.value)
    timerHandle = setInterval(tickTimer, 200)
  })

  onUnmounted(() => {
    if (timerHandle) clearInterval(timerHandle)
  })

  function onDrawTick() {
    playSound('drawTick')
  }

  function onHammerClick() {
    playHammerSold()
  }

  function onActionError() {
    playSound('uiError')
  }

  return {
    onDrawTick,
    onHammerClick,
    onActionError,
  }
}
