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

/** 阵容表头缩写 */
export const POSITION_SHORT: Record<Position, string> = {
  Top: 'TOP',
  Jungle: 'JUG',
  Mid: 'MID',
  Bot: 'BOT',
  Support: 'SUP',
}

export const POSITIONS: Position[] = ['Top', 'Jungle', 'Mid', 'Bot', 'Support']

export const POOL_LETTER_OPTIONS: PoolLetter[] = ['A', 'B', 'C', 'D', 'E']

/** 位置池主题色（用于 UI 标签与舞台高亮） */
export const POSITION_COLORS: Record<Position, string> = {
  Top: '#f97316',
  Jungle: '#84cc16',
  Mid: '#a855f7',
  Bot: '#38bdf8',
  Support: '#f472b6',
}

export const CAPTAIN_AVATAR_GRADIENTS = [
  'linear-gradient(135deg, #4ade80, #16a34a)',
  'linear-gradient(135deg, #38bdf8, #2563eb)',
  'linear-gradient(135deg, #f5c542, #d97706)',
  'linear-gradient(135deg, #c084fc, #7c3aed)',
  'linear-gradient(135deg, #f472b6, #db2777)',
  'linear-gradient(135deg, #fb923c, #ea580c)',
  'linear-gradient(135deg, #2dd4bf, #0d9488)',
  'linear-gradient(135deg, #818cf8, #4f46e5)',
]
