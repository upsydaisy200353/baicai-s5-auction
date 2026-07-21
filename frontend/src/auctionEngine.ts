import type { AuctionPhase } from './types'

/** 公开叫价选人流程 */
export const CEREMONY_STEPS = [
  { id: 'intro', label: '开场介绍' },
  { id: 'pool_draw', label: '全局抽取' },
  { id: 'open_bid', label: '公开叫价' },
  { id: 'winner_reveal', label: '成交公布' },
  { id: 'finished', label: '阵容揭晓' },
] as const

export type CeremonyStepId = (typeof CEREMONY_STEPS)[number]['id']

export function phaseLabel(phase: AuctionPhase): string {
  const map: Record<AuctionPhase, string> = {
    idle: '待开始',
    intro: '开场介绍',
    pool_select: '全局抽取',
    pool_draw: '全局抽取',
    open_bid: '公开叫价',
    winner_reveal: '成交公布',
    player_done: '过渡',
    finished: '仪式结束',
  }
  return map[phase]
}

export function quickIncrements(_currentPrice: number, minNext: number): number[] {
  return [minNext, minNext + 20, minNext + 40, minNext + 80].filter(
    (v, i, arr) => i === 0 || v !== arr[i - 1],
  )
}
