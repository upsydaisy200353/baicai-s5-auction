<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import AppBackground from './components/AppBackground.vue'
import SoundToggle from './components/SoundToggle.vue'
import { useAuth } from './stores/auth'

const router = useRouter()
const route = useRoute()
const { init, user, isAdmin, logout, ready } = useAuth()

const showGuestNav = computed(
  () => !user.value && (route.name === 'spectator' || route.name === 'feedback'),
)

onMounted(init)

function onLogout() {
  logout()
  router.push('/login')
}
</script>

<template>
  <AppBackground />
  <SoundToggle class="global-sound-toggle" />
  <div v-if="ready" class="shell">
    <nav v-if="user" class="nav card fade-in">
      <RouterLink to="/" class="nav-brand">
        <img src="/logo.svg" alt="" class="nav-logo" />
        <span class="nav-brand-text">
          <strong>白菜杯</strong>
          <small>S5 选人仪式</small>
        </span>
      </RouterLink>
      <div class="nav-links">
        <RouterLink to="/" class="nav-link" active-class="active">选人仪式</RouterLink>
        <RouterLink to="/spectator" class="nav-link" active-class="active">观战大屏</RouterLink>
        <RouterLink to="/feedback" class="nav-link" active-class="active">意见反馈</RouterLink>
        <RouterLink v-if="isAdmin" to="/admin" class="nav-link" active-class="active">
          名单管理
        </RouterLink>
        <RouterLink v-if="isAdmin" to="/admin/feedback" class="nav-link" active-class="active">
          查看反馈
        </RouterLink>
      </div>
      <span class="spacer" />
      <span class="user-tag">
        <span class="user-dot" />
        {{ user.displayName }}
      </span>
      <button class="btn-ghost btn-sm" @click="onLogout">退出</button>
    </nav>
    <nav v-else-if="showGuestNav" class="nav card fade-in guest-nav">
      <RouterLink :to="route.name === 'feedback' ? '/feedback' : '/spectator'" class="nav-brand">
        <img src="/logo.svg" alt="" class="nav-logo" />
        <span class="nav-brand-text">
          <strong>白菜杯</strong>
          <small>{{ route.name === 'feedback' ? '意见反馈' : '观战大屏' }}</small>
        </span>
      </RouterLink>
      <span class="spacer" />
      <span class="guest-tag">游客模式</span>
      <RouterLink v-if="route.name !== 'feedback'" to="/feedback" class="btn-ghost btn-sm">意见反馈</RouterLink>
      <RouterLink to="/login" class="btn-ghost btn-sm">登录参赛</RouterLink>
    </nav>
    <main class="main">
      <RouterView />
    </main>
  </div>
  <div v-else class="loading">
    <img src="/logo.svg" alt="" class="loading-logo" />
    <p>加载中…</p>
  </div>
</template>

<style scoped>
.global-sound-toggle {
  position: fixed;
  top: 0.85rem;
  right: 1rem;
  z-index: 1200;
}

.shell {
  max-width: 1440px;
  margin: 0 auto;
  padding: 1rem 1.25rem 2rem;
}

.nav {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.55rem 0.85rem;
  margin-bottom: 1.25rem;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  text-decoration: none;
  color: inherit;
  margin-right: 0.5rem;
}

.nav-logo {
  width: 36px;
  height: 36px;
  filter: drop-shadow(0 0 10px rgba(74, 222, 128, 0.35));
}

.nav-brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.nav-brand-text strong {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 800;
  background: linear-gradient(90deg, var(--cabbage), var(--gold-bright));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-brand-text small {
  font-size: 0.68rem;
  color: var(--text-muted);
  letter-spacing: 0.04em;
}

.nav-links {
  display: flex;
  gap: 0.25rem;
}

.nav-link {
  padding: 0.45rem 0.95rem;
  border-radius: 999px;
  text-decoration: none;
  color: var(--text-muted);
  font-size: 0.84rem;
  font-weight: 600;
  transition: all 0.2s ease;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text);
}

.nav-link.active {
  background: var(--cabbage-dim);
  color: var(--cabbage);
  box-shadow: inset 0 0 0 1px rgba(74, 222, 128, 0.22);
}

.spacer {
  flex: 1;
}

.user-tag {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.user-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--cabbage);
  box-shadow: 0 0 8px var(--cabbage);
  animation: pulse-ring 2s infinite;
}

.btn-sm {
  padding: 0.35rem 0.75rem;
  font-size: 0.8125rem;
}

.guest-tag {
  font-size: 0.8125rem;
  color: #c084fc;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: rgba(168, 85, 247, 0.12);
  border: 1px solid rgba(168, 85, 247, 0.25);
}

.main {
  min-height: 60vh;
}

.loading {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: var(--text-muted);
}

.loading-logo {
  width: 72px;
  height: 72px;
  animation: floatLogo 2.4s ease-in-out infinite;
  filter: drop-shadow(0 0 20px rgba(74, 222, 128, 0.4));
}

@keyframes floatLogo {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
</style>
