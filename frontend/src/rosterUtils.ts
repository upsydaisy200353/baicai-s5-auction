import type { Captain, Player, PoolLetter, RosterEntry, RosterRow } from './types'
import { POOL_LETTERS, POSITION_TO_LETTER } from './constants'

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
