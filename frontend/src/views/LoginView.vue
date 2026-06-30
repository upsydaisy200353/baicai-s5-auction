<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchAccountsHint } from '../api/auth'
import { useAuth } from '../stores/auth'

const router = useRouter()
const { login } = useAuth()

const username = ref('admin')
const password = ref('admin123')
const loading = ref(false)
const error = ref('')
const hint = ref('')

onMounted(async () => {
  try {
    const h = await fetchAccountsHint()
    hint.value = `管理员: ${h.admin.username} / ${h.admin.password} · 队长默认密码: ${h.captainDefaultPassword}`
  } catch {
    hint.value = '请确保后端已启动 (端口 8000)'
  }
})

async function onSubmit() {
  loading.value = true
  error.value = ''
  try {
    await login(username.value.trim(), password.value)
    router.replace('/')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '登录失败'
  } finally {
    loading.value = false
  }
}

function fillCaptain(u: string) {
  username.value = u
  password.value = 'captain123'
}
</script>

<template>
  <div class="login-page">
    <div class="login-card card">
      <h1 class="title">白菜杯选人仪式</h1>
      <p class="subtitle">管理员 / 队长登录</p>

      <form class="form" @submit.prevent="onSubmit">
        <label>
          用户名
          <input v-model="username" autocomplete="username" required />
        </label>
        <label>
          密码
          <input v-model="password" type="password" autocomplete="current-password" required />
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <button class="btn-primary submit" type="submit" :disabled="loading">
          {{ loading ? '登录中…' : '登录' }}
        </button>
      </form>

      <div class="hints">
        <p class="hint-text">{{ hint }}</p>
        <p class="hint-label">队长快捷登录：</p>
        <div class="cap-btns">
          <button type="button" class="btn-ghost cap-btn" @click="fillCaptain('wuyanzu')">吴彦祖</button>
          <button type="button" class="btn-ghost cap-btn" @click="fillCaptain('yazi')">亚子</button>
          <button type="button" class="btn-ghost cap-btn" @click="fillCaptain('caps')">caps</button>
          <button type="button" class="btn-ghost cap-btn" @click="fillCaptain('baiweiyi')">白惟一</button>
          <button type="button" class="btn-ghost cap-btn" @click="fillCaptain('mushroom')">🍄</button>
          <button type="button" class="btn-ghost cap-btn" @click="fillCaptain('xxts')">xxts</button>
          <button type="button" class="btn-ghost cap-btn" @click="fillCaptain('yume')">Yume</button>
          <button type="button" class="btn-ghost cap-btn" @click="fillCaptain('pika')">皮卡</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 80vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 2rem;
}

.title {
  font-size: 1.5rem;
  font-weight: 800;
  text-align: center;
  margin-bottom: 0.25rem;
  background: linear-gradient(90deg, var(--gold), #fde68a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  text-align: center;
  color: var(--text-muted);
  font-size: 0.875rem;
  margin-bottom: 1.5rem;
}

.form label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.form input {
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.55rem 0.75rem;
  color: var(--text);
  font-size: 0.9375rem;
}

.submit {
  width: 100%;
  padding: 0.65rem;
  margin-top: 0.5rem;
}

.error {
  color: var(--red);
  font-size: 0.8125rem;
  margin-bottom: 0.5rem;
}

.hints {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

.hint-text {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

.hint-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.cap-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.cap-btn {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
}
</style>
