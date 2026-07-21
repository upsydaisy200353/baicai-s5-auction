export type Position = 'Top' | 'Jungle' | 'Mid' | 'Bot' | 'Support'

/** 序号前缀 A~E 对应位置池 */
export type PoolLetter = 'A' | 'B' | 'C' | 'D' | 'E'

export interface Player {
  serial: string
  name: string
  startPrice?: number
  originalStartPrice?: number
  buyoutPrice?: number
  /** CSV 档位，如 UR / SSR+ / SR- */
  rating?: string
  weight?: number
  position: Position
  avatar?: string | null
  sold: boolean
  inUnsoldPool?: boolean
  excluded?: boolean
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
  /** CSV 档位，如 UR / SSR+ / SR- */
  rating?: string
  weight?: number
  funds: number | null
  avatar?: string | null
  createdAt?: string
  updatedAt?: string
}

export interface Captain {
  name: string
  /** 实力分（起拍/实力数字，用于排序展示） */
  rating: number
  /** CSV 档位（可选） */
  tier?: string
  funds: number
  team: string[]
  /** 表格中所处分区 A~E */
  poolLetter: PoolLetter
  avatar?: string | null
  alias?: string | null
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
  alias?: string | null
  funds: number | null
  latestBid: number | null
  isLeader: boolean
  canBid: boolean
  canBuyout: boolean
  buyoutUsed: boolean
  skipReason: string | null
  passed: boolean
}

export interface AuctionSettings {
  bidExtensionSeconds: number
  noBidTimeoutSeconds: number
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
  hasBids: boolean
  deadlineMs: number
  noBidDeadlineMs: number
  bidDeadlineMs: number
  bidExtensionSeconds: number
  noBidTimeoutSeconds: number
  timeoutSeconds: number
  secondsRemaining: number
  liveBids: LiveBidEntry[]
  captainRows: CaptainBidRow[]
  captainAliases?: Record<string, string>
}

export interface LastResult {
  player: Player
  winner: string | null
  winnerAlias?: string | null
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
  auctionSettings?: AuctionSettings
  captainAliases?: Record<string, string>
  myAlias?: string | null
  auctionStage?: 'main' | 'unsold'
  unsoldPoolCount?: number
  mainPoolCount?: number
  serverTimeMs?: number
}
