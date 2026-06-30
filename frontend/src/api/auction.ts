import { apiRequest } from './client'
import type { Captain, Player, Position } from '../types'
import type { AuctionPhase, BiddingContext, LastResult, LogEntry } from '../types'

export interface ServerAuctionState {
  phase: AuctionPhase
  captains: Captain[]
  players: Player[]
  poolOrder: Position[]
  currentPoolIndex: number
  currentPool: Position | null
  currentPlayer: Player | null
  bidding: BiddingContext | null
  logs: LogEntry[]
  drawCandidates: Player[]
  lastResult: LastResult | null
  availablePools: Position[]
  bidOrder: string[]
}

export function fetchAuctionState() {
  return apiRequest<ServerAuctionState>('/auction/state')
}

export function startAuction() {
  return apiRequest<ServerAuctionState>('/auction/start', { method: 'POST' })
}

export function beginCeremony() {
  return apiRequest<ServerAuctionState>('/auction/begin', { method: 'POST' })
}

export function setPoolOrder(order: Position[]) {
  return apiRequest<ServerAuctionState>('/auction/set-pool-order', {
    method: 'POST',
    body: JSON.stringify({ order }),
  })
}

export function setBidOrder(captainNames: string[]) {
  return apiRequest<ServerAuctionState>('/auction/set-bid-order', {
    method: 'POST',
    body: JSON.stringify({ captainNames }),
  })
}

export function confirmPool() {
  return apiRequest<ServerAuctionState>('/auction/confirm-pool', { method: 'POST' })
}

export function revealDraw() {
  return apiRequest<ServerAuctionState>('/auction/reveal-draw', { method: 'POST' })
}

export function confirmWinner() {
  return apiRequest<ServerAuctionState>('/auction/confirm-winner', { method: 'POST' })
}

export function submitBid(
  action: 'bid' | 'pass' | 'buyout',
  increment?: number,
  captainName?: string,
) {
  return apiRequest<ServerAuctionState>('/auction/bid', {
    method: 'POST',
    body: JSON.stringify({ action, increment, captainName }),
  })
}

export function resetAuction() {
  return apiRequest<ServerAuctionState>('/auction/reset', { method: 'POST' })
}
