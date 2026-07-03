<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchAccountsHint, type AccountsHint } from '../api/auth'
import { useAuth } from '../stores/auth'

const router = useRouter()
const { login } = useAuth()

const loading = ref(false)
const loadingAs = ref('')
const error = ref('')
const accounts = ref<AccountsHint | null>(null)

onMounted(async () => {
  try {
    accounts.value = await fetchAccountsHint()
  } catch {
    error.value = '请确保后端已启动 (端口 8000)'
  }
})

async function enterAs(username: string) {
  loading.value = true
  loadingAs.value = username
  error.value = ''
  try {
    await login(username)
    router.replace('/')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '进入失败'
  } finally {
    loading.value = false
    loadingAs.value = ''
  }
}
</script>

<template>
  <div class="login-page">
    <section class="login-hero fade-in">
      <div class="hero-bg" aria-hidden="true" />
      <div class="hero-scrim" aria-hidden="true" />
      <div class="hero-content">
        <img src="/logo.svg" alt="" class="hero-logo" />
        <p class="hero-eyebrow">BAICAI CUP · BIDKING MODE</p>
        <h1 class="hero-title">公开叫价选人仪式</h1>
        <p class="hero-desc">
          全员同时叫价 · 倒计时落槌 · 观战大屏
          <br />
          选择身份即可进入，无需密码
        </p>
        <div class="hero-stats">
          <div class="stat">
            <span class="stat-num">8</span>
            <span class="stat-label">队长</span>
          </div>
          <div class="stat">
            <span class="stat-num">5</span>
            <span class="stat-label">位置池</span>
          </div>
          <div class="stat">
            <span class="stat-num">∞</span>
            <span class="stat-label">戏剧性</span>
          </div>
        </div>
      </div>
    </section>

    <div class="login-card card fade-in fade-in-delay-1">
      <h2 class="card-title">进入仪式现场</h2>
      <p class="card-sub">选择你的身份，一键进入</p>

      <p v-if="error" class="error">{{ error }}</p>

      <div v-if="accounts" class="pick-section">
        <p class="pick-label">管理员</p>
        <button
          type="button"
          class="role-btn admin-btn"
          :disabled="loading"
          @click="enterAs(accounts.admin.username)"
        >
          {{ loadingAs === accounts.admin.username ? '进入中…' : accounts.admin.displayName }}
        </button>
      </div>

      <div v-if="accounts" class="pick-section">
        <p class="pick-label">队长</p>
        <div class="cap-btns">
          <button
            v-for="c in accounts.captains"
            :key="c.username"
            type="button"
            class="cap-btn"
            :disabled="loading"
            @click="enterAs(c.username)"
          >
            {{ loadingAs === c.username ? '…' : c.displayName }}
          </button>
        </div>
      </div>

      <p v-else-if="!error" class="loading-hint">加载身份列表…</p>

      <p class="foot-note">现场演示模式 · 免密登录</p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: calc(100vh - 4rem);
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 2rem;
  align-items: stretch;
  padding: 0.5rem 0;
}

.login-hero {
  position: relative;
  border-radius: 20px;
  overflow: hidden;
  min-height: 520px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.45);
}

.hero-bg {
  position: absolute;
  inset: 0;
  background: url('/images/hero-ceremony-bg.png') center / cover no-repeat;
  transform: scale(1.02);
  animation: heroKen 24s ease-in-out infinite alternate;
}

.hero-scrim {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(135deg, rgba(6, 10, 16, 0.82) 0%, rgba(6, 10, 16, 0.45) 45%, rgba(6, 10, 16, 0.88) 100%),
    radial-gradient(ellipse 60% 50% at 30% 40%, rgba(74, 222, 128, 0.12), transparent 60%);
}

.hero-content {
  position: relative;
  z-index: 1;
  padding: 2.5rem 2rem;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

@keyframes heroKen {
  from { transform: scale(1.02) translateX(0); }
  to { transform: scale(1.08) translateX(-12px); }
}

.login-hero .hero-logo {
  width: 96px;
  height: 96px;
  margin-bottom: 1.25rem;
  filter: drop-shadow(0 0 24px rgba(74, 222, 128, 0.45));
  animation: floatLogo 3s ease-in-out infinite;
}

@keyframes floatLogo {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.hero-eyebrow {
  font-family: var(--font-display);
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  color: var(--cabbage);
  margin-bottom: 0.65rem;
}

.hero-title {
  font-family: var(--font-display);
  font-size: clamp(2rem, 4vw, 2.75rem);
  font-weight: 800;
  line-height: 1.15;
  margin-bottom: 0.85rem;
  background: linear-gradient(135deg, #fff 0%, var(--gold-bright) 45%, var(--cabbage) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  color: var(--text-muted);
  font-size: 0.95rem;
  line-height: 1.7;
  margin-bottom: 2rem;
}

.hero-stats {
  display: flex;
  gap: 1.5rem;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.stat-num {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--gold);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  letter-spacing: 0.06em;
}

.login-card {
  padding: 2rem 2rem 1.75rem;
  max-width: 440px;
  justify-self: center;
  align-self: center;
  width: 100%;
  background:
    linear-gradient(160deg, rgba(18, 26, 40, 0.92), rgba(10, 16, 28, 0.88)),
    url('/images/bg-texture.png') center / cover;
  border-color: rgba(255, 255, 255, 0.1);
}

.card-title {
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 700;
  margin-bottom: 0.2rem;
}

.card-sub {
  color: var(--text-muted);
  font-size: 0.875rem;
  margin-bottom: 1.25rem;
}

.error {
  color: var(--red);
  font-size: 0.8125rem;
  margin-bottom: 0.75rem;
}

.pick-section {
  margin-bottom: 1.25rem;
}

.pick-label {
  font-size: 0.72rem;
  color: var(--text-muted);
  letter-spacing: 0.06em;
  margin-bottom: 0.55rem;
  text-transform: uppercase;
}

.role-btn {
  width: 100%;
  padding: 0.7rem 1rem;
  border-radius: var(--radius-sm);
  font-size: 0.95rem;
  font-weight: 600;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.18s ease;
}

.admin-btn {
  background: linear-gradient(135deg, rgba(245, 197, 66, 0.2), rgba(245, 197, 66, 0.08));
  border-color: rgba(245, 197, 66, 0.35);
  color: var(--gold);
}

.admin-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(245, 197, 66, 0.3), rgba(245, 197, 66, 0.12));
  box-shadow: 0 0 20px rgba(245, 197, 66, 0.15);
}

.cap-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.cap-btn {
  font-size: 0.8125rem;
  padding: 0.45rem 0.85rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  color: var(--text);
  cursor: pointer;
  transition: all 0.18s ease;
}

.cap-btn:hover:not(:disabled) {
  border-color: rgba(74, 222, 128, 0.35);
  color: var(--cabbage);
  background: var(--cabbage-dim);
}

.role-btn:disabled,
.cap-btn:disabled {
  opacity: 0.55;
  cursor: wait;
}

.loading-hint {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.foot-note {
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  font-size: 0.72rem;
  color: var(--text-muted);
  text-align: center;
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
    gap: 1.25rem;
  }

  .login-hero {
    min-height: 360px;
  }

  .hero-content {
    text-align: center;
    align-items: center;
    padding: 2rem 1.25rem;
  }

  .hero-content .hero-logo {
    margin-left: auto;
    margin-right: auto;
  }

  .hero-stats {
    justify-content: center;
  }

  .login-card {
    justify-self: center;
    max-width: 100%;
  }
}
</style>
