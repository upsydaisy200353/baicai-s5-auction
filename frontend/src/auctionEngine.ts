import type { AuctionPhase } from './types'

export const MIN_INCREMENT = 10
export const MAX_INCREMENT = 100

/** 公开叫价选人流程 */
export const CEREMONY_STEPS = [
  { id: 'intro', label: '开场介绍' },
  { id: 'pool_select', label: '选择位置池' },
  { id: 'pool_draw', label: '抽取标的' },
  { id: 'open_bid', label: '公开叫价' },
  { id: 'winner_reveal', label: '成交公布' },
  { id: 'finished', label: '阵容揭晓' },
] as const

export type CeremonyStepId = (typeof CEREMONY_STEPS)[number]['id']

export function phaseLabel(phase: AuctionPhase): string {
  const map: Record<AuctionPhase, string> = {
    idle: '待开始',
    intro: '开场介绍',
    pool_select: '选择位置池',
    pool_draw: '抽取标的',
    open_bid: '公开叫价',
    winner_reveal: '成交公布',
    player_done: '过渡',
    finished: '仪式结束',
  }
  return map[phase]
}

export function quickIncrements(currentPrice: number, minNext: number): number[] {
  const inc = currentPrice < 100 ? 10 : currentPrice < 500 ? 10 : currentPrice < 1000 ? 50 : 100
  const base = Math.max(minNext, currentPrice + inc)
  return [base, base + inc, base + inc * 2].filter((v, i, arr) => i === 0 || v !== arr[i - 1])
}
