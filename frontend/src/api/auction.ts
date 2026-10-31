import { apiRequest } from './client'
import type {
  AuctionPhase,
  AuctionSettings,
  Captain,
  LastResult,
  LogEntry,
  OpenBidContext,
  Player,
  Position,
} from '../types'

export interface CaptainOnlineStatus {
  isOnline: boolean
  lastSeen?: string | null
}

export interface ServerAuctionState {
  phase: AuctionPhase
  captains: Captain[]
  players: Player[]
  poolOrder: Position[]
  currentPoolIndex: number
  currentPool: Position | null
  currentPlayer: Player | null
  pendingPick: Player | null
  openBid: OpenBidContext | null
  logs: LogEntry[]
  drawCandidates: Player[]
  drawStartedAtMs?: number | null
  lastResult: LastResult | null
  availablePools: Position[]
  auctionSettings?: AuctionSettings
  captainAliases?: Record<string, string>
  myAlias?: string | null
  auctionStage?: 'main' | 'unsold'
  unsoldPoolCount?: number
  mainPoolCount?: number
  captainOnline?: Record<string, CaptainOnlineStatus>
  serverTimeMs?: number
}

async function withServerTimeEstimate(
  request: () => Promise<ServerAuctionState>,
): Promise<ServerAuctionState> {
  const requestStartedAt = performance.now()
  const state = await request()
  if (typeof state.serverTimeMs === 'number') {
    state.serverTimeMs += Math.round((performance.now() - requestStartedAt) / 2)
  }
  return state
}

export function fetchAuctionState() {
  return withServerTimeEstimate(() => apiRequest<ServerAuctionState>('/auction/state'))
}

/** 观战大屏 — 无需登录 */
export interface AuctionHistoryRecord {
  id: string
  completedAt: string
  state: {
    phase: AuctionPhase
    captains: Captain[]
    players: Player[]
    poolOrder?: Position[]
    logs: LogEntry[]
    auctionStage?: 'main' | 'unsold'
  }
}

export function fetchAuctionHistory() {
  return apiRequest<AuctionHistoryRecord[]>('/auction/history')
}

export interface AuctionResultSnapshot {
  id: string
  completedAt: string
  state: {
    phase: AuctionPhase
    captains: Captain[]
    players: Player[]
    poolOrder?: Position[]
    auctionStage?: 'main' | 'unsold'
  }
}

export function fetchLatestAuctionResult() {
  return fetch('/api/auction/latest-result').then(async (res) => {
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json() as Promise<AuctionResultSnapshot | null>
  })
}

export function fetchSpectatorState() {
  return withServerTimeEstimate(async () => {
    const res = await fetch('/api/auction/spectator')
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail ?? `HTTP ${res.status}`)
    }
    return res.json() as Promise<ServerAuctionState>
  })
}

export function startAuction() {
  return withServerTimeEstimate(() => apiRequest<ServerAuctionState>('/auction/start', { method: 'POST' }))
}

export function beginCeremony() {
  return withServerTimeEstimate(() => apiRequest<ServerAuctionState>('/auction/begin', { method: 'POST' }))
}

export function revealDraw() {
  return withServerTimeEstimate(() => apiRequest<ServerAuctionState>('/auction/reveal-draw', { method: 'POST' }))
}

export function hammerAuction() {
  return withServerTimeEstimate(() => apiRequest<ServerAuctionState>('/auction/hammer', { method: 'POST' }))
}

export function confirmWinner() {
  return withServerTimeEstimate(() => apiRequest<ServerAuctionState>('/auction/confirm-winner', { method: 'POST' }))
}

export function submitOpenBid(
  action: 'bid' | 'pass' | 'buyout',
  opts: { playerSerial: string; amount?: number; captainName?: string },
) {
  return withServerTimeEstimate(() => apiRequest<ServerAuctionState>('/auction/bid', {
    method: 'POST',
    body: JSON.stringify({ action, ...opts }),
  }))
}

export function resetAuction() {
  return withServerTimeEstimate(() => apiRequest<ServerAuctionState>('/auction/reset', { method: 'POST' }))
}

export function updateAuctionSettings(settings: AuctionSettings) {
  return withServerTimeEstimate(() => apiRequest<ServerAuctionState>('/auction/settings', {
    method: 'POST',
    body: JSON.stringify(settings),
  }))
}
