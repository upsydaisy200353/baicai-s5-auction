/** 位置池常量（A~E） */

import type { PoolLetter, Position } from './types'

export const POOL_LETTERS: Record<PoolLetter, Position> = {
  A: 'Top',
  B: 'Jungle',
  C: 'Mid',
  D: 'Bot',
  E: 'Support',
}

export const POSITION_TO_LETTER: Record<Position, PoolLetter> = {
  Top: 'A',
  Jungle: 'B',
  Mid: 'C',
  Bot: 'D',
  Support: 'E',
}

export const POSITION_NAMES: Record<Position, string> = {
  Top: '上单',
  Jungle: '打野',
  Mid: '中单',
  Bot: '下路',
  Support: '辅助',
}

export const POSITIONS: Position[] = ['Top', 'Jungle', 'Mid', 'Bot', 'Support']

export const POOL_LETTER_OPTIONS: PoolLetter[] = ['A', 'B', 'C', 'D', 'E']
