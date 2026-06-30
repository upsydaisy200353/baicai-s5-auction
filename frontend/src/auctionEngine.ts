import { reactive } from 'vue'
import {
  POSITION_NAMES,
  POSITIONS,
} from './constants'
import { isAuctionablePlayer } from './rosterUtils'
import type {
  AuctionPhase,
  AuctionSnapshot,
  BidAction,
  BiddingContext,
  Captain,
  LastResult,
  LogEntry,
  Player,
  Position,
} from './types'

export const MIN_INCREMENT = 10
export const MAX_INCREMENT = 100

/** S4 选人仪式流程（参考白菜杯官方录像） */
export const CEREMONY_STEPS = [
  { id: 'intro', label: '开场介绍' },
  { id: 'pool_select', label: '设定池顺序' },
  { id: 'pool_announce', label: '进入位置池' },
  { id: 'pool_draw', label: '随机抽取选手' },
  { id: 'bidding', label: '拍卖竞价' },
  { id: 'winner_reveal', label: '成交公布' },
  { id: 'finished', label: '阵容揭晓' },
] as const

function deepClone<T>(v: T): T {
  return JSON.parse(JSON.stringify(v))
}

function nowTime(): string {
  return new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

export class AuctionEngine {
  phase: AuctionPhase = 'idle'
  captains: Captain[] = []
  players: Player[] = []
  private captainNames = new Set<string>()
  poolOrder: Position[] = []
  currentPoolIndex = 0
  currentPool: Position | null = null
  currentPlayer: Player | null = null
  drawCandidates: Player[] = []
  lastResult: LastResult | null = null
  logs: LogEntry[] = []
  private logId = 0

  private roundNum = 0
  private currentPrice = 0
  private highestBidder: Captain | null = null
  private lastIncrement = MIN_INCREMENT
  private turnIndex = 0
  private order: Captain[] = []
  private raisedThisRound = false
  private lastBuyout = false
  bidding: BiddingContext | null = null

  private remainingPools: Position[] = []
  private pendingPick: Player | null = null

  addLog(text: string, type: LogEntry['type'] = 'info') {
    this.logs.push({ id: ++this.logId, time: nowTime(), text, type })
  }

  reset() {
    this.phase = 'idle'
    this.captains = []
    this.players = []
    this.captainNames = new Set()
    this.poolOrder = []
    this.currentPoolIndex = 0
    this.currentPool = null
    this.currentPlayer = null
    this.drawCandidates = []
    this.lastResult = null
    this.logs = []
    this.logId = 0
    this.bidding = null
    this.remainingPools = [...POSITIONS]
    this.pendingPick = null
    this.lastBuyout = false
  }

  get snapshot(): AuctionSnapshot {
    return {
      phase: this.phase,
      captains: deepClone(this.captains),
      players: deepClone(this.players),
      poolOrder: [...this.poolOrder],
      currentPoolIndex: this.currentPoolIndex,
      currentPool: this.currentPool,
      currentPlayer: this.currentPlayer ? deepClone(this.currentPlayer) : null,
      bidding: this.bidding ? deepClone(this.bidding) : null,
      logs: [...this.logs],
      drawCandidates: deepClone(this.drawCandidates),
      lastResult: this.lastResult ? deepClone(this.lastResult) : null,
    }
  }

  activeCaptains(): Captain[] {
    return this.captains.filter((c) => c.funds > 0)
  }

  loadRoster(players: Player[], captains: Captain[]) {
    this.players = deepClone(players)
    this.captains = deepClone(captains.map((c) => ({ ...c, team: [...c.team] })))
    this.captainNames = new Set(captains.map((c) => c.name))
  }

  availablePlayers(position: Position): Player[] {
    return this.players.filter(
      (p) =>
        p.position === position &&
        !p.sold &&
        isAuctionablePlayer(p, this.captainNames),
    )
  }

  /** 仪式开始：先进入开场介绍 */
  start() {
    this.reset()
    this.phase = 'intro'
    this.addLog('白菜杯选人仪式开始', 'phase')
    this.addLog('8 位队长将通过拍卖竞价组建战队', 'info')
  }

  /** 开场结束 → 等待管理员设定池顺序 */
  beginPoolSelect() {
    if (this.phase !== 'intro') return
    this.phase = 'pool_select'
    this.poolOrder = []
    this.remainingPools = [...POSITIONS]
    this.addLog('第一阶段：管理员确定位置池拍卖顺序', 'phase')
  }

  get availablePools(): Position[] {
    if (this.phase !== 'pool_select') return []
    return [...this.remainingPools]
  }

  setPoolOrder(order: Position[]) {
    if (this.phase !== 'pool_select') return
    if (order.length !== POSITIONS.length || new Set(order).size !== POSITIONS.length) return
    this.poolOrder = [...order]
    this.remainingPools = []
    const labels = order.map((p) => POSITION_NAMES[p]).join(' → ')
    this.addLog(`拍卖顺序：${labels}`, 'phase')
    this.currentPoolIndex = 0
    this.announcePool()
  }

  private announcePool() {
    if (this.currentPoolIndex >= this.poolOrder.length) {
      this.phase = 'finished'
      this.addLog('选人仪式圆满结束，各队阵容已确定', 'phase')
      return
    }
    this.currentPool = this.poolOrder[this.currentPoolIndex]!
    this.phase = 'pool_announce'
    this.addLog(
      `进入【${POSITION_NAMES[this.currentPool]}】位置池（第 ${this.currentPoolIndex + 1}/${this.poolOrder.length} 个）`,
      'phase',
    )
  }

  /** 仪式：确认进入位置池 → 开始抽签 */
  confirmPoolEnter() {
    if (this.phase !== 'pool_announce') return
    this.startDraw()
  }

  private startDraw() {
    if (!this.currentPool) return
    const pool = this.availablePlayers(this.currentPool)
    if (pool.length === 0) {
      this.addLog(`${POSITION_NAMES[this.currentPool]} 池已空，进入下一位置`, 'info')
      this.currentPoolIndex++
      this.announcePool()
      return
    }
    if (this.activeCaptains().length === 0) {
      this.phase = 'finished'
      this.addLog('所有队长资金耗尽，仪式结束', 'warn')
      return
    }

    const idx = Math.floor(Math.random() * pool.length)
    this.pendingPick = pool[idx]!
    this.drawCandidates = deepClone(pool)
    this.currentPlayer = null
    this.phase = 'pool_draw'
    this.addLog(`随机选择程序启动 — ${POSITION_NAMES[this.currentPool]} 池 ${pool.length} 人待抽`, 'info')
  }

  /** 抽签动画结束 → 揭晓选手 */
  revealDraw() {
    if (this.phase !== 'pool_draw' || !this.pendingPick) return
    this.currentPlayer = this.pendingPick
    this.addLog(
      `揭晓：${this.currentPlayer.serial} ${this.currentPlayer.name} | 起拍 ${this.currentPlayer.startPrice}w / 一口价 ${this.currentPlayer.buyoutPrice}w`,
      'phase',
    )
    this.pendingPick = null
    this.beginBidding()
  }

  private beginBidding() {
    if (!this.currentPlayer) return
    this.phase = 'bidding'
    this.roundNum = 0
    this.currentPrice = this.currentPlayer.startPrice
    this.highestBidder = null
    this.lastIncrement = MIN_INCREMENT
    this.addLog(`拍卖开始 — ${this.currentPlayer.name}`, 'phase')
    this.startNewRound()
  }

  private startNewRound() {
    if (!this.currentPlayer) return
    this.roundNum++
    this.raisedThisRound = false
    this.turnIndex = 0

    const active = this.activeCaptains()
    this.order =
      this.roundNum === 1
        ? [...active].sort((a, b) => b.rating - a.rating)
        : [...active].sort((a, b) => a.funds - b.funds)

    const orderText = this.order.map((c) => c.name).join(' → ')
    this.addLog(
      this.roundNum === 1
        ? `第 1 轮竞价（实力强→弱）：${orderText}`
        : `第 ${this.roundNum} 轮竞价（资金少→多）：${orderText}`,
      'info',
    )

    this.advanceTurn()
  }

  private advanceTurn() {
    if (!this.currentPlayer || this.phase !== 'bidding') return

    while (this.turnIndex < this.order.length) {
      const cap = this.order[this.turnIndex]!
      this.turnIndex++

      if (this.highestBidder && cap.name === this.highestBidder.name) continue
      if (cap.funds < this.currentPrice + MIN_INCREMENT) {
        this.addLog(`[${cap.name}] 资金不足，跳过`, 'warn')
        continue
      }

      this.bidding = {
        player: deepClone(this.currentPlayer),
        currentPrice: this.currentPrice,
        highestBidder: this.highestBidder?.name ?? null,
        roundNum: this.roundNum,
        lastIncrement: this.lastIncrement,
        minNextBid: this.currentPrice + MIN_INCREMENT,
        minRaise: MIN_INCREMENT,
        isFirstRound: this.roundNum === 1,
        turnCaptain: deepClone(cap),
        order: deepClone(this.order),
        passedCaptains: [],
      }
      return
    }

    if (!this.raisedThisRound) {
      this.finishPlayerAuction()
    } else {
      this.startNewRound()
    }
  }

  submitBid(action: BidAction) {
    if (this.phase !== 'bidding' || !this.bidding || !this.currentPlayer) return

    const cap = this.captains.find((c) => c.name === action.captain)
    if (!cap || cap.name !== this.bidding.turnCaptain.name) return

    if (action.action === 'pass') {
      this.addLog(`[${cap.name}] 放弃`, 'info')
      this.bidding = null
      this.advanceTurn()
      return
    }

    if (action.action === 'buyout') {
      if (this.roundNum !== 1) {
        this.addLog(`[${cap.name}] 一口价仅首轮可用`, 'warn')
        this.bidding = null
        this.advanceTurn()
        return
      }
      if (cap.funds < this.currentPlayer.buyoutPrice) {
        this.addLog(`[${cap.name}] 一口价资金不足`, 'warn')
        this.bidding = null
        this.advanceTurn()
        return
      }
      this.completeSale(cap, this.currentPlayer.buyoutPrice, true)
      return
    }

    let inc = Math.max(MIN_INCREMENT, Math.min(action.increment ?? MIN_INCREMENT, MAX_INCREMENT))
    if (this.roundNum > 1 && inc < this.lastIncrement) inc = this.lastIncrement

    let newPrice = this.currentPrice + inc
    if (newPrice > this.currentPlayer.buyoutPrice) newPrice = this.currentPlayer.buyoutPrice
    if (newPrice > cap.funds) {
      this.addLog(`[${cap.name}] 出价超出剩余资金`, 'warn')
      this.bidding = null
      this.advanceTurn()
      return
    }

    this.currentPrice = newPrice
    this.lastIncrement = inc
    this.highestBidder = cap
    this.raisedThisRound = true
    this.addLog(`[${cap.name}] 出价 ${newPrice}w (+${inc}w)`, 'bid')
    this.bidding = null
    this.advanceTurn()
  }

  autoBid() {
    if (!this.bidding || !this.currentPlayer) return
    const cap = this.bidding.turnCaptain
    const action = computeAutoBid(
      cap,
      this.currentPrice,
      this.lastIncrement,
      this.currentPlayer.buyoutPrice,
      this.roundNum === 1,
    )
    if (!action) {
      this.submitBid({ captain: cap.name, action: 'pass' })
    } else {
      this.submitBid(action)
    }
  }

  private completeSale(cap: Captain, price: number, buyout: boolean) {
    if (!this.currentPlayer) return
    const player = this.players.find((p) => p.serial === this.currentPlayer!.serial)!
    player.sold = true
    player.finalPrice = price
    player.winner = cap.name
    cap.funds -= price
    cap.team.push(player.name)
    this.lastBuyout = buyout

    if (buyout) {
      this.addLog(`[${cap.name}] ★ 一口价 ${price}w 买断！`, 'buyout')
    }
    this.showWinnerReveal(player, cap.name, price)
  }

  private finishPlayerAuction() {
    if (!this.currentPlayer) return
    if (this.highestBidder) {
      this.completeSale(this.highestBidder, this.currentPrice, false)
    } else {
      this.addLog(`${this.currentPlayer.name} 流拍`, 'warn')
      this.showWinnerReveal(this.currentPlayer, null, null)
    }
  }

  private showWinnerReveal(player: Player, winner: string | null, price: number | null) {
    this.lastResult = {
      player: deepClone(player),
      winner,
      price,
      buyout: this.lastBuyout,
    }
    this.bidding = null
    this.currentPlayer = null
    this.phase = 'winner_reveal'
    if (winner && price != null) {
      this.addLog(`成交：${winner} 以 ${price}w 签下 ${player.name}`, 'win')
    }
  }

  /** 成交公布结束 → 下一位或下一池 */
  confirmWinner() {
    if (this.phase !== 'winner_reveal') return
    this.lastResult = null
    this.phase = 'player_done'
    this.startDraw()
  }

  finishPoolSelection() {
    if (this.phase === 'pool_select') {
      this.setPoolOrder([...POSITIONS])
    }
  }
}

export function computeAutoBid(
  cap: Captain,
  currentPrice: number,
  lastIncrement: number,
  buyoutPrice: number,
  isFirstRound: boolean,
): BidAction | null {
  const inc = Math.max(lastIncrement, MIN_INCREMENT)
  const target = Math.min(currentPrice + inc, buyoutPrice)
  if (target > cap.funds) return null

  const ratio = buyoutPrice ? currentPrice / buyoutPrice : 1
  if (ratio >= 0.85 && Math.random() < 0.7) return null
  if (isFirstRound && cap.funds >= buyoutPrice && Math.random() < 0.05) {
    return { captain: cap.name, action: 'buyout' }
  }
  if (Math.random() < 0.45) {
    return { captain: cap.name, action: 'bid', increment: inc }
  }
  return null
}

export function createAuctionEngine() {
  return reactive(new AuctionEngine()) as AuctionEngine
}
