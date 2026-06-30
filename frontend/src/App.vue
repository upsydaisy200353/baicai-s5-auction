<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuth } from './stores/auth'

const router = useRouter()
const { init, user, isAdmin, logout, ready } = useAuth()

onMounted(init)

function onLogout() {
  logout()
  router.push('/login')
}
</script>

<template>
  <div v-if="ready" class="shell">
    <nav v-if="user" class="nav card">
      <RouterLink to="/" class="nav-link" active-class="active">选人仪式</RouterLink>
      <RouterLink v-if="isAdmin" to="/admin" class="nav-link" active-class="active">
        名单管理
      </RouterLink>
      <span class="spacer" />
      <span class="user-tag">{{ user.displayName }}</span>
      <button class="btn-ghost btn-sm" @click="onLogout">退出</button>
    </nav>
    <main class="main">
      <RouterView />
    </main>
  </div>
  <div v-else class="loading">加载中…</div>
</template>

<style scoped>
.shell {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.25rem;
}

.nav {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  margin-bottom: 1rem;
}

.nav-link {
  padding: 0.45rem 1rem;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-muted);
  font-size: 0.875rem;
  font-weight: 600;
}

.nav-link:hover {
  background: var(--bg-hover);
  color: var(--text);
}

.nav-link.active {
  background: var(--accent-glow);
  color: var(--accent);
}

.spacer {
  flex: 1;
}

.user-tag {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.btn-sm {
  padding: 0.35rem 0.65rem;
  font-size: 0.8125rem;
}

.main {
  min-height: 60vh;
}

.loading {
  text-align: center;
  padding: 4rem;
  color: var(--text-muted);
}
</style>
