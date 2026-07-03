export type Position = 'Top' | 'Jungle' | 'Mid' | 'Bot' | 'Support'

/** 序号前缀 A~E 对应位置池 */
export type PoolLetter = 'A' | 'B' | 'C' | 'D' | 'E'

export interface Player {
  serial: string
  name: string
  startPrice?: number
  buyoutPrice?: number
  position: Position
  avatar?: string | null
  sold: boolean
  finalPrice: number | null
  winner: string | null
}

export interface RosterEntry {
  id: number
  sortOrder: number
  identity: 'player' | 'captain'
  serial: string | null
  name: string
  poolLetter: PoolLetter
  position: Position
  startPrice: number
  buyoutPrice: number | null
  funds: number | null
  avatar?: string | null
  createdAt?: string
  updatedAt?: string
}

export interface Captain {
  name: string
  rating: number
  funds: number
  team: string[]
  /** 表格中所处分区 A~E */
  poolLetter: PoolLetter
  avatar?: string | null
}

export type RosterRow =
  | { kind: 'player'; data: Player }
  | { kind: 'captain'; data: Captain }

export type AuctionPhase =
  | 'idle'
  | 'intro'
  | 'pool_select'
  | 'pool_draw'
  | 'open_bid'
  | 'winner_reveal'
  | 'player_done'
  | 'finished'

export type BidActionType = 'bid' | 'pass' | 'buyout'

export interface LiveBidEntry {
  id: number
  captain: string
  amount: number
  time: string
}

export interface CaptainBidRow {
  name: string
  funds: number
  latestBid: number | null
  isLeader: boolean
  canBid: boolean
  skipReason: string | null
  passed: boolean
}

export interface OpenBidContext {
  player: Player
  eligibleCaptains: Captain[]
  currentPrice: number
  currentLeader: string | null
  leaderCaptain: Captain | null
  minNextBid: number
  minIncrement: number
  startPrice: number
  buyoutPrice: number | null
  deadlineMs: number
  timeoutSeconds: number
  secondsRemaining: number
  liveBids: LiveBidEntry[]
  captainRows: CaptainBidRow[]
}

export interface LastResult {
  player: Player
  winner: string | null
  price: number | null
}

export interface LogEntry {
  id: number
  time: string
  text: string
  type: 'info' | 'bid' | 'buyout' | 'win' | 'phase' | 'warn'
}

export interface AuctionSnapshot {
  phase: AuctionPhase
  captains: Captain[]
  players: Player[]
  poolOrder: Position[]
  currentPoolIndex: number
  currentPool: Position | null
  currentPlayer: Player | null
  openBid: OpenBidContext | null
  logs: LogEntry[]
  drawCandidates: Player[]
  lastResult: LastResult | null
  availablePools?: Position[]
}
