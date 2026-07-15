import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from './api/client'
import { fetchMe } from './api/auth'
import AuctionView from './views/AuctionView.vue'
import FeedbackAdmin from './views/FeedbackAdmin.vue'
import FeedbackView from './views/FeedbackView.vue'
import RosterAdmin from './views/RosterAdmin.vue'
import SpectatorView from './views/SpectatorView.vue'
import LoginView from './views/LoginView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
    { path: '/spectator', name: 'spectator', component: SpectatorView, meta: { public: true } },
    { path: '/feedback', name: 'feedback', component: FeedbackView, meta: { public: true } },
    { path: '/', name: 'auction', component: AuctionView, meta: { requiresAuth: true } },
    {
      path: '/admin',
      name: 'admin',
      component: RosterAdmin,
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/feedback',
      name: 'admin-feedback',
      component: FeedbackAdmin,
      meta: { requiresAuth: true, requiresAdmin: true },
    },
  ],
})

router.beforeEach(async (to) => {
  const token = getToken()
  if (to.meta.public) {
    if (token && to.name === 'login') return '/'
    return true
  }
  if (!token) return '/login'
  if (to.meta.requiresAdmin) {
    try {
      const user = await fetchMe()
      if (user.role !== 'admin') return '/'
    } catch {
      return '/login'
    }
  }
  return true
})
