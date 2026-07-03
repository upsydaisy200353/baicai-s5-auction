import { apiRequest } from './client'

export interface AuthUser {
  id: number
  username: string
  role: 'admin' | 'captain'
  captainName: string | null
  displayName: string
}

export interface LoginResponse {
  token: string
  user: AuthUser
}

export interface AccountsHint {
  admin: { username: string; displayName: string; role: string }
  captains: { username: string; displayName: string }[]
}

export function login(username: string) {
  return apiRequest<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username }),
  })
}

export function fetchMe() {
  return apiRequest<AuthUser>('/auth/me')
}

export function fetchAccountsHint() {
  return apiRequest<AccountsHint>('/auth/accounts-hint')
}
