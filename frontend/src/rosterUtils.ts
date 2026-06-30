import type { Captain, Player, PoolLetter, Position, RosterEntry, RosterRow } from './types'
import { POOL_LETTERS, POSITION_NAMES, POSITION_TO_LETTER } from './constants'

export function entriesToPlayers(entries: RosterEntry[]): Player[] {
  return entries
    .filter((e) => e.identity === 'player')
    .map((e) => ({
      serial: e.serial || '',
      name: e.name,
      startPrice: e.startPrice,
      buyoutPrice: e.buyoutPrice ?? 0,
      position: e.position,
      sold: false,
      finalPrice: null,
      winner: null,
    }))
}

export function entriesToCaptains(entries: RosterEntry[]): Captain[] {
  return entries
    .filter((e) => e.identity === 'captain')
    .map((e) => ({
      name: e.name,
      rating: e.startPrice,
      funds: e.funds ?? 0,
      poolLetter: e.poolLetter,
      team: [],
    }))
}

export function buildRosterRowsFromEntries(entries: RosterEntry[]): RosterRow[] {
  return [...entries]
    .sort((a, b) => a.sortOrder - b.sortOrder)
    .map((e) =>
      e.identity === 'captain'
        ? {
            kind: 'captain' as const,
            data: {
              name: e.name,
              rating: e.startPrice,
              funds: e.funds ?? 0,
              poolLetter: e.poolLetter,
              team: [],
            },
          }
        : {
            kind: 'player' as const,
            data: {
              serial: e.serial || '',
              name: e.name,
              startPrice: e.startPrice,
              buyoutPrice: e.buyoutPrice ?? 0,
              position: e.position,
              sold: false,
              finalPrice: null,
              winner: null,
            },
          },
    )
}

export function isAuctionablePlayer(player: Player, captainNames: Set<string>): boolean {
  return !captainNames.has(player.name)
}

export function poolLetterFromPosition(position: Player['position']): PoolLetter {
  return POSITION_TO_LETTER[position]
}

export function positionFromPoolLetter(letter: PoolLetter) {
  return POOL_LETTERS[letter]
}

/** 队长已占用的位置：本人分区 + 已拍下的队员 */
export function captainOccupiedPositions(
  cap: Captain,
  players: Player[],
): Position[] {
  const positions = new Set<Position>()
  positions.add(POOL_LETTERS[cap.poolLetter])
  for (const name of cap.team) {
    const p = players.find((pl) => pl.name === name)
    if (p) positions.add(p.position)
  }
  return [...positions]
}

export function captainCanBidForPosition(
  cap: Captain,
  position: Position,
  players: Player[],
): boolean {
  if (cap.funds <= 0) return false
  return !captainOccupiedPositions(cap, players).includes(position)
}

export function captainSkipReason(
  cap: Captain,
  position: Position,
  players: Player[],
): string | null {
  if (cap.funds <= 0) return '资金不足'
  if (POOL_LETTERS[cap.poolLetter] === position) {
    return `本人为${POSITION_NAMES[position]}`
  }
  if (cap.team.some((n) => players.find((p) => p.name === n)?.position === position)) {
    return `已有${POSITION_NAMES[position]}选手`
  }
  return null
}
