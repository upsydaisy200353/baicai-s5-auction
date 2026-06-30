import { apiRequest } from './client'
import type { Captain, Player, RosterEntry } from '../types'

export interface RosterResponse {
  entries: RosterEntry[]
  players: Player[]
  captains: Captain[]
}

export function fetchRoster(): Promise<RosterResponse> {
  return apiRequest('/roster')
}

export function fetchEntries(): Promise<RosterEntry[]> {
  return apiRequest('/roster/entries')
}

export function createEntry(
  payload: Omit<RosterEntry, 'id' | 'position' | 'createdAt' | 'updatedAt'>,
): Promise<RosterEntry> {
  return apiRequest('/roster/entries', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateEntry(
  id: number,
  payload: Partial<Omit<RosterEntry, 'id' | 'createdAt' | 'updatedAt'>>,
): Promise<RosterEntry> {
  return apiRequest(`/roster/entries/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteEntry(id: number): Promise<{ ok: boolean }> {
  return apiRequest(`/roster/entries/${id}`, { method: 'DELETE' })
}

export function reseedRoster(): Promise<RosterResponse> {
  return apiRequest('/roster/reseed', { method: 'POST' })
}
