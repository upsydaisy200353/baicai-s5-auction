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
  captainCount?: number
}

export interface AdminUserRow {
  id: number
  username: string
  role: 'admin' | 'captain'
  captainName: string | null
  displayName: string
  passwordPlain?: string
}

export function login(username: string, password: string) {
  return apiRequest<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export function changePassword(currentPassword: string, newPassword: string) {
  return apiRequest<{ ok: boolean }>('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({ currentPassword, newPassword }),
  })
}

export function fetchAdminUsers() {
  return apiRequest<AdminUserRow[]>('/admin/users')
}

export function adminSetPassword(userId: number, newPassword: string) {
  return apiRequest<{ ok: boolean; username: string }>(`/admin/users/${userId}/password`, {
    method: 'PUT',
    body: JSON.stringify({ newPassword }),
  })
}

export function fetchMe() {
  return apiRequest<AuthUser>('/auth/me')
}

export function fetchAccountsHint() {
  return apiRequest<AccountsHint>('/auth/accounts-hint')
}
