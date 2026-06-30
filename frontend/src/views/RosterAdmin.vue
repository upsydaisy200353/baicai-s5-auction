<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import {
  createEntry,
  deleteEntry,
  fetchEntries,
  reseedRoster,
  updateEntry,
} from '../api/roster'
import {
  POOL_LETTER_OPTIONS,
  POOL_LETTERS,
  POSITION_NAMES,
} from '../constants'
import type { PoolLetter, RosterEntry } from '../types'

const entries = ref<RosterEntry[]>([])
const loading = ref(true)
const savingId = ref<number | null>(null)
const message = ref('')
const error = ref('')

const newRow = reactive({
  identity: 'player' as 'player' | 'captain',
  serial: '',
  name: '',
  poolLetter: 'A' as PoolLetter,
  startPrice: 100,
  buyoutPrice: 300,
  funds: 2500,
  sortOrder: 999,
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    entries.value = await fetchEntries()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function posLabel(letter: PoolLetter) {
  return `${letter}·${POSITION_NAMES[POOL_LETTERS[letter]]}`
}

async function save(entry: RosterEntry) {
  savingId.value = entry.id
  message.value = ''
  error.value = ''
  try {
    const updated = await updateEntry(entry.id, {
      sortOrder: entry.sortOrder,
      identity: entry.identity,
      serial: entry.serial,
      name: entry.name,
      poolLetter: entry.poolLetter,
      startPrice: entry.startPrice,
      buyoutPrice: entry.buyoutPrice,
      funds: entry.funds,
    })
    const idx = entries.value.findIndex((e) => e.id === entry.id)
    if (idx >= 0) entries.value[idx] = updated
    message.value = `已保存：${updated.name}`
  } catch (e) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    savingId.value = null
  }
}

async function remove(entry: RosterEntry) {
  if (!confirm(`确定删除 ${entry.name}？`)) return
  try {
    await deleteEntry(entry.id)
    entries.value = entries.value.filter((e) => e.id !== entry.id)
    message.value = '已删除'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '删除失败'
  }
}

async function addRow() {
  message.value = ''
  error.value = ''
  try {
    const payload = {
      sortOrder: newRow.sortOrder,
      identity: newRow.identity,
      serial: newRow.identity === 'player' ? newRow.serial : null,
      name: newRow.name,
      poolLetter: newRow.poolLetter,
      startPrice: newRow.startPrice,
      buyoutPrice: newRow.identity === 'player' ? newRow.buyoutPrice : null,
      funds: newRow.identity === 'captain' ? newRow.funds : null,
    }
    const created = await createEntry(payload)
    entries.value.push(created)
    entries.value.sort((a, b) => a.sortOrder - b.sortOrder)
    message.value = `已添加：${created.name}`
    newRow.name = ''
    newRow.serial = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : '添加失败'
  }
}

async function resetDefault() {
  if (!confirm('恢复为默认名单？当前修改将全部丢失。')) return
  try {
    const data = await reseedRoster()
    entries.value = data.entries
    message.value = '已恢复默认名单'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '恢复失败'
  }
}

function onIdentityChange(entry: RosterEntry) {
  if (entry.identity === 'captain') {
    entry.buyoutPrice = null
    entry.serial = null
  } else {
    entry.funds = null
    if (entry.buyoutPrice == null) entry.buyoutPrice = entry.startPrice * 2
  }
}
</script>

<template>
  <div class="admin">
    <header class="admin-header">
      <div>
        <h1 class="title">名单管理</h1>
        <p class="subtitle">数据保存在 SQLite 数据库，修改后拍卖页刷新即可生效</p>
      </div>
      <div class="actions">
        <button class="btn-ghost" :disabled="loading" @click="load">刷新</button>
        <button class="btn-danger" @click="resetDefault">恢复默认</button>
      </div>
    </header>

    <div v-if="message" class="flash ok">{{ message }}</div>
    <div v-if="error" class="flash err">{{ error }}</div>
    <div v-if="loading" class="flash info">加载中…</div>

    <div class="card add-form">
      <h3>新增条目</h3>
      <div class="form-grid">
        <label>
          身份
          <select v-model="newRow.identity">
            <option value="player">选手</option>
            <option value="captain">队长</option>
          </select>
        </label>
        <label v-if="newRow.identity === 'player'">
          序号
          <input v-model="newRow.serial" placeholder="如 A7" />
        </label>
        <label>
          ID / 名称
          <input v-model="newRow.name" placeholder="名称" />
        </label>
        <label>
          位置池
          <select v-model="newRow.poolLetter">
            <option v-for="l in POOL_LETTER_OPTIONS" :key="l" :value="l">
              {{ posLabel(l) }}
            </option>
          </select>
        </label>
        <label>
          {{ newRow.identity === 'captain' ? '实力分' : '起拍价' }}
          <input v-model.number="newRow.startPrice" type="number" min="0" />
        </label>
        <label v-if="newRow.identity === 'player'">
          一口价
          <input v-model.number="newRow.buyoutPrice" type="number" min="0" />
        </label>
        <label v-else>
          竞拍资金
          <input v-model.number="newRow.funds" type="number" min="0" />
        </label>
        <label>
          排序
          <input v-model.number="newRow.sortOrder" type="number" min="1" />
        </label>
      </div>
      <button class="btn-primary" @click="addRow">添加</button>
    </div>

    <div class="table-wrap card">
      <table class="edit-table">
        <thead>
          <tr>
            <th>排序</th>
            <th>身份</th>
            <th>序号</th>
            <th>名称</th>
            <th>位置池</th>
            <th>起拍/实力</th>
            <th>一口价</th>
            <th>资金</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in entries" :key="entry.id" :class="entry.identity">
            <td><input v-model.number="entry.sortOrder" type="number" class="input-sm" /></td>
            <td>
              <select
                v-model="entry.identity"
                @change="onIdentityChange(entry)"
              >
                <option value="player">选手</option>
                <option value="captain">队长</option>
              </select>
            </td>
            <td>
              <input
                v-if="entry.identity === 'player'"
                v-model="entry.serial"
                class="input-sm"
              />
              <span v-else class="badge badge-gold">队长</span>
            </td>
            <td><input v-model="entry.name" /></td>
            <td>
              <select v-model="entry.poolLetter">
                <option v-for="l in POOL_LETTER_OPTIONS" :key="l" :value="l">
                  {{ posLabel(l) }}
                </option>
              </select>
            </td>
            <td><input v-model.number="entry.startPrice" type="number" class="input-sm" /></td>
            <td>
              <input
                v-if="entry.identity === 'player'"
                v-model.number="entry.buyoutPrice"
                type="number"
                class="input-sm"
              />
              <span v-else>—</span>
            </td>
            <td>
              <input
                v-if="entry.identity === 'captain'"
                v-model.number="entry.funds"
                type="number"
                class="input-sm"
              />
              <span v-else>—</span>
            </td>
            <td class="ops">
              <button
                class="btn-primary btn-sm"
                :disabled="savingId === entry.id"
                @click="save(entry)"
              >
                保存
              </button>
              <button class="btn-ghost btn-sm" @click="remove(entry)">删</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.title {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text);
}

.subtitle {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.actions {
  display: flex;
  gap: 0.5rem;
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
  background: rgba(59, 130, 246, 0.1);
  color: #93c5fd;
}

.add-form {
  margin-bottom: 1rem;
}

.add-form h3 {
  margin-bottom: 0.75rem;
  font-size: 0.9375rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.form-grid label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

input,
select {
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  padding: 0.4rem 0.5rem;
  font-size: 0.8125rem;
}

.table-wrap {
  overflow-x: auto;
}

.edit-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.edit-table th {
  text-align: left;
  padding: 0.5rem;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
}

.edit-table td {
  padding: 0.35rem 0.5rem;
  border-bottom: 1px solid rgba(45, 58, 79, 0.4);
  vertical-align: middle;
}

.edit-table tr.captain {
  background: rgba(245, 158, 11, 0.04);
}

.input-sm {
  width: 72px;
}

.ops {
  display: flex;
  gap: 0.35rem;
  white-space: nowrap;
}

.btn-sm {
  padding: 0.3rem 0.55rem;
  font-size: 0.75rem;
}
</style>
