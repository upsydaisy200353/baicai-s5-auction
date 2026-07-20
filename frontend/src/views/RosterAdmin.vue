<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { apiRequest } from '../api/client'
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
const activeTab = ref<'players' | 'captains'>('players')
const auctionLocked = ref(false)

const players = computed(() =>
  entries.value
    .filter((e) => e.identity === 'player')
    .sort((a, b) => a.sortOrder - b.sortOrder),
)

const captains = computed(() =>
  entries.value
    .filter((e) => e.identity === 'captain')
    .sort((a, b) => a.sortOrder - b.sortOrder),
)

const newPlayer = reactive({
  serial: '',
  name: '',
  poolLetter: 'A' as PoolLetter,
  startPrice: 100,
  buyoutPrice: 300,
  rating: 'SSR',
  weight: 1,
  sortOrder: 999,
})

const newCaptain = reactive({
  name: '',
  poolLetter: 'A' as PoolLetter,
  startPrice: 100,
  rating: 'SSR',
  funds: 2500,
  sortOrder: 999,
})

async function loadMeta() {
  try {
    const meta = await apiRequest<{ auctionInProgress: boolean }>('/meta')
    auctionLocked.value = meta.auctionInProgress
  } catch {
    auctionLocked.value = false
  }
}

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

onMounted(async () => {
  await Promise.all([load(), loadMeta()])
})

function posLabel(letter: PoolLetter) {
  return `${letter}·${POSITION_NAMES[POOL_LETTERS[letter]]}`
}

function nextSortOrder(identity: 'player' | 'captain') {
  const list = identity === 'player' ? players.value : captains.value
  if (list.length === 0) return 1
  return Math.max(...list.map((e) => e.sortOrder)) + 1
}

async function save(entry: RosterEntry) {
  if (auctionLocked.value) return
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
      rating: entry.rating ?? '',
      weight: entry.weight ?? 1,
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
  if (auctionLocked.value) return
  if (!confirm(`确定删除 ${entry.name}？`)) return
  try {
    await deleteEntry(entry.id)
    entries.value = entries.value.filter((e) => e.id !== entry.id)
    message.value = '已删除'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '删除失败'
  }
}

async function addPlayer() {
  if (auctionLocked.value) return
  message.value = ''
  error.value = ''
  try {
    const created = await createEntry({
      sortOrder: newPlayer.sortOrder || nextSortOrder('player'),
      identity: 'player',
      serial: newPlayer.serial,
      name: newPlayer.name,
      poolLetter: newPlayer.poolLetter,
      startPrice: newPlayer.startPrice,
      buyoutPrice: newPlayer.buyoutPrice,
      rating: newPlayer.rating,
      weight: newPlayer.weight,
      funds: null,
    })
    entries.value.push(created)
    message.value = `已添加选手：${created.name}`
    newPlayer.name = ''
    newPlayer.serial = ''
    newPlayer.sortOrder = nextSortOrder('player')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '添加失败'
  }
}

async function addCaptain() {
  if (auctionLocked.value) return
  message.value = ''
  error.value = ''
  try {
    const created = await createEntry({
      sortOrder: newCaptain.sortOrder || nextSortOrder('captain'),
      identity: 'captain',
      serial: null,
      name: newCaptain.name,
      poolLetter: newCaptain.poolLetter,
      startPrice: newCaptain.startPrice,
      buyoutPrice: null,
      rating: newCaptain.rating,
      funds: newCaptain.funds,
    })
    entries.value.push(created)
    message.value = `已添加队长：${created.name}`
    newCaptain.name = ''
    newCaptain.sortOrder = nextSortOrder('captain')
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
</script>

<template>
  <div class="admin">
    <header class="admin-header">
      <div>
        <h1 class="title">名单管理</h1>
        <p class="subtitle">
          选手与队长分开管理；点「保存」后写入数据库
        </p>
      </div>
      <div class="actions">
        <button class="btn-ghost" :disabled="loading" @click="load">刷新</button>
        <button class="btn-danger" :disabled="auctionLocked" @click="resetDefault">恢复默认</button>
      </div>
    </header>

    <div v-if="auctionLocked" class="flash warn">
      仪式进行中，名单已锁定。请先重置仪式后再修改。
    </div>

    <div v-if="message" class="flash ok">{{ message }}</div>
    <div v-if="error" class="flash err">{{ error }}</div>
    <div v-if="loading" class="flash info">加载中…</div>

    <div class="tabs">
      <button
        class="tab"
        :class="{ active: activeTab === 'players' }"
        @click="activeTab = 'players'"
      >
        选手
        <span class="tab-count">{{ players.length }}</span>
      </button>
      <button
        class="tab tab-captain"
        :class="{ active: activeTab === 'captains' }"
        @click="activeTab = 'captains'"
      >
        队长
        <span class="tab-count">{{ captains.length }}</span>
      </button>
    </div>

    <!-- 选手管理 -->
    <section v-show="activeTab === 'players'" class="section">
      <div class="card add-form">
        <h3>新增选手</h3>
        <div class="form-grid">
          <label>
            序号
            <input v-model="newPlayer.serial" placeholder="如 A7" />
          </label>
          <label>
            名称
            <input v-model="newPlayer.name" placeholder="选手 ID" />
          </label>
          <label>
            位置池
            <select v-model="newPlayer.poolLetter">
              <option v-for="l in POOL_LETTER_OPTIONS" :key="l" :value="l">
                {{ posLabel(l) }}
              </option>
            </select>
          </label>
          <label>
            起拍价
            <input v-model.number="newPlayer.startPrice" type="number" min="0" />
          </label>
          <label>
            一口价
            <input v-model.number="newPlayer.buyoutPrice" type="number" min="0" />
          </label>
          <label>
            评级
            <input v-model="newPlayer.rating" placeholder="UR / SSR / SR+" />
          </label>
          <label>
            抽签权重
            <input v-model.number="newPlayer.weight" type="number" min="1" />
          </label>
          <label>
            排序
            <input v-model.number="newPlayer.sortOrder" type="number" min="1" />
          </label>
        </div>
        <button class="btn-primary" :disabled="auctionLocked" @click="addPlayer">添加选手</button>
      </div>

      <div class="table-wrap card">
        <table class="edit-table">
          <thead>
            <tr>
              <th>排序</th>
              <th>序号</th>
              <th>名称</th>
              <th>位置池</th>
              <th>起拍价</th>
              <th>一口价</th>
              <th>评级</th>
              <th>权重</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="players.length === 0">
              <td colspan="9" class="empty">暂无选手</td>
            </tr>
            <tr v-for="entry in players" :key="entry.id">
              <td><input v-model.number="entry.sortOrder" type="number" class="input-sm" /></td>
              <td><input v-model="entry.serial" class="input-sm input-serial" /></td>
              <td><input v-model="entry.name" /></td>
              <td>
                <select v-model="entry.poolLetter">
                  <option v-for="l in POOL_LETTER_OPTIONS" :key="l" :value="l">
                    {{ posLabel(l) }}
                  </option>
                </select>
              </td>
              <td><input v-model.number="entry.startPrice" type="number" class="input-sm" /></td>
              <td><input v-model.number="entry.buyoutPrice" type="number" class="input-sm" /></td>
              <td><input v-model="entry.rating" class="input-sm" placeholder="SSR" /></td>
              <td><input v-model.number="entry.weight" type="number" class="input-sm" min="1" /></td>
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
    </section>

    <!-- 队长管理 -->
    <section v-show="activeTab === 'captains'" class="section section-captain">
      <div class="card add-form">
        <h3>新增队长</h3>
        <div class="form-grid">
          <label>
            名称
            <input v-model="newCaptain.name" placeholder="队长 ID" />
          </label>
          <label>
            位置池
            <select v-model="newCaptain.poolLetter">
              <option v-for="l in POOL_LETTER_OPTIONS" :key="l" :value="l">
                {{ posLabel(l) }}
              </option>
            </select>
          </label>
          <label>
            实力分
            <input v-model.number="newCaptain.startPrice" type="number" min="0" />
          </label>
          <label>
            评级
            <input v-model="newCaptain.rating" placeholder="UR / SSR" />
          </label>
          <label>
            竞拍资金
            <input v-model.number="newCaptain.funds" type="number" min="0" />
          </label>
          <label>
            排序
            <input v-model.number="newCaptain.sortOrder" type="number" min="1" />
          </label>
        </div>
        <button class="btn-primary btn-captain" :disabled="auctionLocked" @click="addCaptain">添加队长</button>
      </div>

      <div class="table-wrap card">
        <table class="edit-table edit-table-captain">
          <thead>
            <tr>
              <th>排序</th>
              <th>名称</th>
              <th>位置池</th>
              <th>实力分</th>
              <th>评级</th>
              <th>竞拍资金</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="captains.length === 0">
              <td colspan="7" class="empty">暂无队长</td>
            </tr>
            <tr v-for="entry in captains" :key="entry.id">
              <td><input v-model.number="entry.sortOrder" type="number" class="input-sm" /></td>
              <td><input v-model="entry.name" class="name-input" /></td>
              <td>
                <select v-model="entry.poolLetter">
                  <option v-for="l in POOL_LETTER_OPTIONS" :key="l" :value="l">
                    {{ posLabel(l) }}
                  </option>
                </select>
              </td>
              <td><input v-model.number="entry.startPrice" type="number" class="input-sm" /></td>
              <td><input v-model="entry.rating" class="input-sm" placeholder="SSR" /></td>
              <td><input v-model.number="entry.funds" type="number" class="input-sm" /></td>
              <td class="ops">
                <button
                  class="btn-primary btn-sm btn-captain"
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
    </section>
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

.flash.warn {
  background: var(--gold-dim);
  color: var(--gold);
  border: 1px solid rgba(245, 197, 66, 0.25);
}

.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.tab {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.55rem 1rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg-hover);
  color: var(--text-muted);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.tab:hover {
  color: var(--text);
}

.tab.active {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.35);
  color: #93c5fd;
}

.tab-captain.active {
  background: rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.35);
  color: var(--gold);
}

.tab-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.25rem;
  height: 1.25rem;
  padding: 0 0.35rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 0.7rem;
  font-weight: 700;
}

.section {
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.add-form {
  margin-bottom: 1rem;
}

.add-form h3 {
  margin-bottom: 0.75rem;
  font-size: 0.9375rem;
}

.section-captain .add-form h3 {
  color: var(--gold);
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

.edit-table-captain tbody tr {
  background: rgba(245, 158, 11, 0.04);
}

.edit-table-captain .name-input {
  color: var(--gold);
  font-weight: 600;
}

.empty {
  text-align: center;
  color: var(--text-muted);
  padding: 1.5rem !important;
}

.input-sm {
  width: 72px;
}

.input-serial {
  width: 56px;
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

.btn-captain {
  background: linear-gradient(135deg, #d97706, #b45309);
  border-color: rgba(245, 158, 11, 0.4);
}

.btn-captain:hover:not(:disabled) {
  filter: brightness(1.08);
}
</style>
