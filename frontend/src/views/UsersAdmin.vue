<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import {
  adminSetPassword,
  changePassword,
  fetchAdminUsers,
  type AdminUserRow,
} from '../api/auth'
import { useAuth } from '../stores/auth'

const { user } = useAuth()

const users = ref<AdminUserRow[]>([])
const loading = ref(true)
const message = ref('')
const error = ref('')
const savingId = ref<number | null>(null)
const draftPasswords = reactive<Record<number, string>>({})

const myForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})
const mySaving = ref(false)

async function load() {
  loading.value = true
  error.value = ''
  try {
    users.value = await fetchAdminUsers()
    for (const u of users.value) {
      if (!(u.id in draftPasswords)) draftPasswords[u.id] = ''
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function setUserPassword(u: AdminUserRow) {
  const pw = (draftPasswords[u.id] || '').trim()
  if (pw.length < 4) {
    error.value = '新密码至少 4 位'
    return
  }
  savingId.value = u.id
  message.value = ''
  error.value = ''
  try {
    await adminSetPassword(u.id, pw)
    draftPasswords[u.id] = ''
    message.value = `已更新 ${u.displayName}（${u.username}）的密码`
  } catch (e) {
    error.value = e instanceof Error ? e.message : '修改失败'
  } finally {
    savingId.value = null
  }
}

async function saveMyPassword() {
  if (myForm.newPassword.length < 4) {
    error.value = '新密码至少 4 位'
    return
  }
  if (myForm.newPassword !== myForm.confirmPassword) {
    error.value = '两次输入的新密码不一致'
    return
  }
  mySaving.value = true
  message.value = ''
  error.value = ''
  try {
    await changePassword(myForm.currentPassword, myForm.newPassword)
    myForm.currentPassword = ''
    myForm.newPassword = ''
    myForm.confirmPassword = ''
    message.value = '已更新你的登录密码'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '修改失败'
  } finally {
    mySaving.value = false
  }
}
</script>

<template>
  <div class="users-admin">
    <header class="header">
      <div>
        <h1 class="title">账号与密码</h1>
        <p class="subtitle">管理员可重置任意账号密码；也可修改自己的登录密码</p>
      </div>
      <button class="btn-ghost" :disabled="loading" @click="load">刷新</button>
    </header>

    <div v-if="message" class="flash ok">{{ message }}</div>
    <div v-if="error" class="flash err">{{ error }}</div>
    <div v-if="loading" class="flash info">加载中…</div>

    <section class="card section">
      <h2 class="section-title">修改我的密码</h2>
      <p class="hint">当前登录：{{ user?.displayName }}（{{ user?.username }}）</p>
      <form class="my-form" @submit.prevent="saveMyPassword">
        <label>
          当前密码
          <input v-model="myForm.currentPassword" type="password" autocomplete="current-password" />
        </label>
        <label>
          新密码
          <input v-model="myForm.newPassword" type="password" autocomplete="new-password" />
        </label>
        <label>
          确认新密码
          <input v-model="myForm.confirmPassword" type="password" autocomplete="new-password" />
        </label>
        <button class="btn-primary" type="submit" :disabled="mySaving">
          {{ mySaving ? '保存中…' : '保存我的密码' }}
        </button>
      </form>
    </section>

    <section class="card section">
      <h2 class="section-title">重置账号密码</h2>
      <p class="hint">直接设置新密码，无需对方旧密码。队长改密后需重新登录。</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>显示名</th>
              <th>用户名</th>
              <th>角色</th>
              <th>新密码</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.displayName }}</td>
              <td><code>{{ u.username }}</code></td>
              <td>
                <span class="role" :class="u.role">{{ u.role === 'admin' ? '管理员' : '队长' }}</span>
              </td>
              <td>
                <input
                  v-model="draftPasswords[u.id]"
                  type="password"
                  placeholder="至少 4 位"
                  class="pw-input"
                />
              </td>
              <td>
                <button
                  class="btn-primary btn-sm"
                  :disabled="savingId === u.id"
                  @click="setUserPassword(u)"
                >
                  {{ savingId === u.id ? '…' : '设密' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.users-admin {
  max-width: 960px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.title {
  font-size: 1.5rem;
  font-weight: 800;
}

.subtitle {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.flash {
  padding: 0.6rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.flash.ok {
  background: var(--green-dim);
  color: var(--green);
}

.flash.err {
  background: var(--red-dim);
  color: var(--red);
}

.flash.info {
  background: rgba(56, 189, 248, 0.08);
  color: #7dd3fc;
}

.section {
  padding: 1.1rem 1.25rem;
  margin-bottom: 1rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 0.35rem;
}

.hint {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.85rem;
}

.my-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
  align-items: end;
}

.my-form label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.my-form input,
.pw-input {
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  padding: 0.4rem 0.55rem;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

th,
td {
  text-align: left;
  padding: 0.55rem 0.45rem;
  border-bottom: 1px solid var(--border);
}

th {
  color: var(--text-muted);
  font-size: 0.72rem;
  font-weight: 600;
}

code {
  font-size: 0.8rem;
  color: var(--cabbage);
}

.role {
  font-size: 0.72rem;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
}

.role.admin {
  background: rgba(245, 197, 66, 0.12);
  color: var(--gold);
}

.role.captain {
  background: var(--cabbage-dim);
  color: var(--cabbage);
}

.btn-sm {
  padding: 0.3rem 0.7rem;
  font-size: 0.8rem;
}

.pw-input {
  width: 140px;
}
</style>
