import { reactive, computed } from 'vue'
import { getToken, setToken } from '../api/client'
import { fetchMe, login as apiLogin, type AuthUser } from '../api/auth'

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

  async function login(username: string) {
    const res = await apiLogin(username)
    setToken(res.token)
    state.user = res.user
    return res.user
  }

  function logout() {
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
