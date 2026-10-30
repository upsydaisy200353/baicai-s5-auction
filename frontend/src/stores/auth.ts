import { reactive, computed } from 'vue'
import { getToken, setToken } from '../api/client'
import { fetchMe, login as apiLogin, logout as apiLogout, type AuthUser } from '../api/auth'

const state = reactive({
  user: null as AuthUser | null,
  ready: false,
})

export function useAuth() {
  const isLoggedIn = computed(() => !!state.user)
  const isAdmin = computed(() => state.user?.role === 'admin')
  const isCaptain = computed(() => state.user?.role === 'captain')
  const captainName = computed(() => state.user?.captainName ?? null)

  async function init() {
    if (!getToken()) {
      state.user = null
      state.ready = true
      return
    }
    try {
      state.user = await fetchMe()
    } catch {
      setToken(null)
      state.user = null
    } finally {
      state.ready = true
    }
  }

  async function login(username: string, password: string) {
    const res = await apiLogin(username, password)
    setToken(res.token)
    state.user = res.user
    return res.user
  }

  async function logout() {
    try {
      await apiLogout()
    } catch {
      // 本地退出仍应完成；服务端在线状态会在心跳超时后过期。
    }
    setToken(null)
    state.user = null
  }

  return {
    state,
    user: computed(() => state.user),
    ready: computed(() => state.ready),
    isLoggedIn,
    isAdmin,
    isCaptain,
    captainName,
    init,
    login,
    logout,
  }
}
