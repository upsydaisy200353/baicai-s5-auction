const TOKEN_KEY = 'auction_token'
const LOGOUT_REASON_KEY = 'auction_logout_reason'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export function consumeLogoutReason(): string | null {
  const reason = sessionStorage.getItem(LOGOUT_REASON_KEY)
  if (reason) sessionStorage.removeItem(LOGOUT_REASON_KEY)
  return reason
}

export function authHeaders(): HeadersInit {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...init?.headers,
    },
  })
  if (res.status === 401) {
    let msg = '登录已失效，请重新登录'
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') msg = body.detail
    } catch {
      // ignore
    }
    sessionStorage.setItem(LOGOUT_REASON_KEY, msg)
    setToken(null)
    if (!window.location.pathname.startsWith('/login')) {
      window.location.href = '/login'
    }
    throw new Error(msg)
  }
  if (!res.ok) {
    let msg = res.statusText
    const text = await res.text()
    try {
      const body = JSON.parse(text)
      msg = body.detail || body.message || msg
    } catch {
      if (text) msg = text
    }
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
  return res.json()
}
