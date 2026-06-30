export type Position = 'Top' | 'Jungle' | 'Mid' | 'Bot' | 'Support'

/** 序号前缀 A~E 对应位置池 */
export type PoolLetter = 'A' | 'B' | 'C' | 'D' | 'E'

export interface Player {
  serial: string
  name: string
  startPrice: number
  buyoutPrice: number
  position: Position
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
}

export type RosterRow =
  | { kind: 'player'; data: Player }
  | { kind: 'captain'; data: Captain }

export type AuctionPhase =
  | 'idle'
  | 'intro'
  | 'pool_select'
  | 'pool_announce'
  | 'pool_draw'
  | 'bidding'
  | 'winner_reveal'
  | 'player_done'
  | 'finished'

export type BidActionType = 'bid' | 'pass' | 'buyout'

export interface BidAction {
  captain: string
  action: BidActionType
  increment?: number
}

export interface LogEntry {
  id: number
  time: string
  text: string
  type: 'info' | 'bid' | 'buyout' | 'win' | 'phase' | 'warn'
}

export interface BiddingContext {
  player: Player
  currentPrice: number
  highestBidder: string | null
  roundNum: number
  lastIncrement: number
  minNextBid: number
  minRaise: number
  isFirstRound: boolean
  turnCaptain: Captain
  order: Captain[]
  passedCaptains: string[]
}

export interface LastResult {
  player: Player
  winner: string | null
  price: number | null
  buyout: boolean
}

export interface AuctionSnapshot {
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
}
