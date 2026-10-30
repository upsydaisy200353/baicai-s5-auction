import { apiRequest, setToken } from './client'

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
  captainCount?: number
}

export interface AdminUserRow {
  id: number
  username: string
  role: 'admin' | 'captain'
  captainName: string | null
  displayName: string
}

export function login(username: string, password: string) {
  return apiRequest<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export async function changePassword(currentPassword: string, newPassword: string) {
  const result = await apiRequest<{ ok: boolean; token: string }>('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({ currentPassword, newPassword }),
  })
  setToken(result.token)
  return result
}

export function fetchAdminUsers() {
  return apiRequest<AdminUserRow[]>('/admin/users')
}

export async function adminSetPassword(userId: number, newPassword: string) {
  const result = await apiRequest<{ ok: boolean; username: string; token?: string }>(`/admin/users/${userId}/password`, {
    method: 'PUT',
    body: JSON.stringify({ newPassword }),
  })
  if (result.token) setToken(result.token)
  return result
}

export function logout() {
  return apiRequest<{ ok: boolean }>('/auth/logout', { method: 'POST' })
}

export function fetchMe() {
  return apiRequest<AuthUser>('/auth/me')
}

export function fetchAccountsHint() {
  return apiRequest<AccountsHint>('/auth/accounts-hint')
}
