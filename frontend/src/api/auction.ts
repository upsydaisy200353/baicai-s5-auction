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
  lastResult: LastResult | null
  availablePools: Position[]
  auctionSettings?: AuctionSettings
  captainAliases?: Record<string, string>
  myAlias?: string | null
  auctionStage?: 'main' | 'unsold'
  unsoldPoolCount?: number
  mainPoolCount?: number
  captainOnline?: Record<string, CaptainOnlineStatus>
}

export function fetchAuctionState() {
  return apiRequest<ServerAuctionState>('/auction/state')
}

/** 观战大屏 — 无需登录 */
export function fetchSpectatorState() {
  return fetch('/api/auction/spectator').then(async (res) => {
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail ?? `HTTP ${res.status}`)
    }
    return res.json() as Promise<ServerAuctionState>
  })
}

export function startAuction() {
  return apiRequest<ServerAuctionState>('/auction/start', { method: 'POST' })
}

export function beginCeremony() {
  return apiRequest<ServerAuctionState>('/auction/begin', { method: 'POST' })
}

export function revealDraw() {
  return apiRequest<ServerAuctionState>('/auction/reveal-draw', { method: 'POST' })
}

export function hammerAuction() {
  return apiRequest<ServerAuctionState>('/auction/hammer', { method: 'POST' })
}

export function confirmWinner() {
  return apiRequest<ServerAuctionState>('/auction/confirm-winner', { method: 'POST' })
}

export function submitOpenBid(
  action: 'bid' | 'pass' | 'buyout',
  opts?: { amount?: number; captainName?: string },
) {
  return apiRequest<ServerAuctionState>('/auction/bid', {
    method: 'POST',
    body: JSON.stringify({ action, ...opts }),
  })
}

export function resetAuction() {
  return apiRequest<ServerAuctionState>('/auction/reset', { method: 'POST' })
}

export function updateAuctionSettings(settings: AuctionSettings) {
  return apiRequest<ServerAuctionState>('/auction/settings', {
    method: 'POST',
    body: JSON.stringify(settings),
  })
}
