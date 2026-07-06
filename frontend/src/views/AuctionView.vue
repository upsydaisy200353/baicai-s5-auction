<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import {
  beginCeremony,
  confirmWinner,
  fetchAuctionState,
  hammerAuction,
  resetAuction as apiResetAuction,
  revealDraw,
  selectPool,
  startAuction,
  submitOpenBid,
  updateAuctionSettings,
  type ServerAuctionState,
} from '../api/auction'
import AdminCeremonyBar from '../components/AdminCeremonyBar.vue'
import CeremonyOverlay from '../components/CeremonyOverlay.vue'
import CeremonyTimeline from '../components/CeremonyTimeline.vue'
import LogPanel from '../components/LogPanel.vue'
import OpenBidPanel from '../components/OpenBidPanel.vue'
import SpectatorBoard from '../components/SpectatorBoard.vue'
import { useAuth } from '../stores/auth'
import type { Position } from '../types'

const { isAdmin, isCaptain, captainName, user } = useAuth()

const state = ref<ServerAuctionState | null>(null)
const loading = ref(true)
const error = ref('')
const actionMsg = ref('')
const proxyCaptain = ref<string | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

const overlayPhases = ['intro', 'pool_draw', 'winner_reveal', 'finished']

const myCaptainRow = computed(() => {
  if (!state.value?.openBid || !captainName.value) return null
  return state.value.openBid.captainRows.find((r) => r.name === captainName.value) ?? null
})

const canSubmitBid = computed(() => {
  if (!state.value?.openBid || state.value.phase !== 'open_bid') return false
  if (isAdmin.value) {
    const name = proxyCaptain.value
    if (!name) return false
    const row = state.value.openBid.captainRows.find((r) => r.name === name)
    return !!row?.canBid && !row.passed
  }
  if (!isCaptain.value || !captainName.value) return false
  const row = myCaptainRow.value
  return !!row?.canBid && !row.passed
})

const hasPassed = computed(() => {
  if (isAdmin.value && proxyCaptain.value) {
    const row = state.value?.openBid?.captainRows.find((r) => r.name === proxyCaptain.value)
    return !!row?.passed
  }
  return !!myCaptainRow.value?.passed
})

const canHammer = computed(
  () =>
    isAdmin.value &&
    state.value?.phase === 'open_bid' &&
    !!state.value.openBid?.currentLeader &&
    (state.value.openBid?.currentPrice ?? 0) > 0,
)

watch(
  () => state.value?.openBid,
  () => {
    if (!state.value?.openBid) return
    const eligible = state.value.openBid.captainRows.filter((r) => r.canBid && !r.passed)
    if (isAdmin.value && eligible.length) {
      if (!proxyCaptain.value || !eligible.some((r) => r.name === proxyCaptain.value)) {
        proxyCaptain.value = eligible[0]!.name
      }
    }
  },
  { deep: true },
)

async function refresh() {
  try {
    state.value = await fetchAuctionState()
    error.value = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : '同步失败'
  } finally {
    loading.value = false
  }
}

async function runAction(fn: () => Promise<ServerAuctionState>, label?: string) {
  actionMsg.value = ''
  try {
    state.value = await fn()
    if (label) actionMsg.value = label
  } catch (e) {
    actionMsg.value = e instanceof Error ? e.message : '操作失败'
  }
}

onMounted(async () => {
  await refresh()
  pollTimer = setInterval(refresh, 1200)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

async function onStart() {
  await runAction(startAuction)
}

async function onBegin() {
  await runAction(beginCeremony)
}

async function onSelectPool(pool: Position) {
  await runAction(() => selectPool(pool))
}

async function onRevealDraw() {
  await runAction(revealDraw)
}

async function onConfirmWinner() {
  await runAction(confirmWinner)
}

async function onHammer() {
  await runAction(hammerAuction, '已落槌')
}

async function onReset() {
  await runAction(apiResetAuction, '已重置')
}

async function onUpdateSettings(settings: { bidExtensionSeconds: number; noBidTimeoutSeconds: number }) {
  await runAction(() => updateAuctionSettings(settings), '计时已更新')
}

async function onBid(amount: number) {
  await runAction(() =>
    submitOpenBid('bid', {
      amount,
      captainName: isAdmin.value ? proxyCaptain.value ?? undefined : undefined,
    }),
  )
}

async function onPass() {
  await runAction(() =>
    submitOpenBid('pass', {
      captainName: isAdmin.value ? proxyCaptain.value ?? undefined : undefined,
    }),
  )
}

async function onBuyout() {
  const buyout = state.value?.openBid?.buyoutPrice
  if (!buyout) return
  await runAction(() =>
    submitOpenBid('buyout', {
      amount: buyout,
      captainName: isAdmin.value ? proxyCaptain.value ?? undefined : undefined,
    }),
  )
}
</script>

<template>
  <div class="auction-view">
    <div v-if="loading && !state" class="banner info">同步拍卖状态…</div>
    <div v-if="error" class="banner error">{{ error }}</div>
    <div v-if="actionMsg" class="banner warn">{{ actionMsg }}</div>

    <template v-if="state">
      <CeremonyOverlay
        v-if="overlayPhases.includes(state.phase)"
        :phase="state.phase"
        :captains="state.captains"
        :current-pool="state.currentPool"
        :pool-order="state.poolOrder"
        :draw-candidates="state.drawCandidates"
        :last-result="state.lastResult"
        :is-admin="isAdmin"
        @begin="onBegin"
        @reveal-draw="onRevealDraw"
        @confirm-winner="onConfirmWinner"
      />

      <!-- 待开始 -->
      <template v-if="state.phase === 'idle'">
        <header class="idle-header card">
          <img src="/logo.svg" alt="" class="idle-logo" />
          <div>
            <p class="idle-eyebrow">BAICAI CUP · LIVE AUCTION</p>
            <h1 class="idle-title">公开叫价选人现场</h1>
            <p class="idle-sub">
              <span class="user-pill">{{ user?.displayName }}</span>
              <span class="role-tag">{{ isAdmin ? '管理员' : '队长' }}</span>
            </p>
          </div>
          <div class="idle-actions">
            <template v-if="isAdmin">
              <button class="btn-primary btn-start" @click="onStart">开始仪式</button>
              <router-link to="/admin" class="btn-ghost">名单管理</router-link>
            </template>
            <router-link to="/spectator" class="btn-ghost">观战大屏 ↗</router-link>
          </div>
        </header>
        <p class="idle-hint">全员同时叫价 · 倒计时落槌 · 最高价者得</p>
      </template>

      <!-- 仪式进行中：观战大屏 -->
      <template v-else>
        <CeremonyTimeline :phase="state.phase" />

        <AdminCeremonyBar
          v-if="isAdmin && !overlayPhases.includes(state.phase)"
          :phase="state.phase"
          :available-pools="state.availablePools"
          :pool-order="state.poolOrder"
          :can-hammer="canHammer"
          :auction-settings="state.auctionSettings"
          @select-pool="onSelectPool"
          @hammer="onHammer"
          @reset="onReset"
          @update-settings="onUpdateSettings"
        />

        <SpectatorBoard
          :phase="state.phase"
          :captains="state.captains"
          :current-pool="state.currentPool"
          :current-player="state.currentPlayer"
          :open-bid="state.openBid"
          :pool-order="state.poolOrder"
          :is-admin="isAdmin"
        >
          <template v-if="state.phase === 'open_bid'" #bidPanel>
            <div v-if="isAdmin" class="proxy-row">
              <label class="proxy-label">
                代出价队长
                <select v-model="proxyCaptain" class="proxy-select">
                  <option
                    v-for="row in state.openBid?.captainRows.filter((r) => r.canBid || r.passed)"
                    :key="row.name"
                    :value="row.name"
                  >
                    {{ row.name }}{{ row.passed ? '（已放弃）' : '' }}
                  </option>
                </select>
              </label>
            </div>

            <OpenBidPanel
              v-if="state.openBid && (canSubmitBid || hasPassed)"
              :open-bid="state.openBid"
              :can-submit="canSubmitBid"
              :has-passed="hasPassed"
              :proxy-mode="isAdmin"
              :proxy-captain-name="proxyCaptain"
              :self-captain-name="captainName"
              :is-admin="isAdmin"
              @bid="onBid"
              @pass="onPass"
              @buyout="onBuyout"
            />

            <div v-else-if="isCaptain && !canSubmitBid" class="banner info compact">
              {{ myCaptainRow?.skipReason ?? '当前无法参与本场竞拍' }}
            </div>
          </template>
        </SpectatorBoard>

        <details v-if="isAdmin" class="admin-log card">
          <summary>操作日志</summary>
          <LogPanel :logs="state.logs" />
        </details>
      </template>
    </template>
  </div>
</template>

<style scoped>
.auction-view {
  width: 100%;
}

.banner {
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  margin-bottom: 1rem;
  font-size: 0.875rem;
  border: 1px solid transparent;
}

.banner.info {
  background: rgba(56, 189, 248, 0.08);
  color: #7dd3fc;
  border-color: rgba(56, 189, 248, 0.2);
}

.banner.error {
  background: var(--red-dim);
  color: var(--red);
}

.banner.warn {
  background: var(--gold-dim);
  color: var(--gold);
}

.banner.compact {
  margin-bottom: 0;
  padding: 0.5rem 0.75rem;
}

.idle-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.idle-logo {
  width: 56px;
  height: 56px;
}

.idle-eyebrow {
  font-family: var(--font-display);
  font-size: 0.65rem;
  letter-spacing: 0.14em;
  color: var(--purple);
}

.idle-title {
  font-family: var(--font-display);
  font-size: 1.65rem;
  font-weight: 800;
}

.idle-sub {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.35rem;
  font-size: 0.8125rem;
}

.user-pill {
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
}

.role-tag {
  padding: 0.12rem 0.5rem;
  border-radius: 999px;
  background: var(--cabbage-dim);
  color: var(--cabbage);
  font-size: 0.7rem;
  font-weight: 600;
}

.idle-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.btn-start {
  padding: 0.65rem 1.5rem;
  font-size: 1rem;
}

.idle-hint {
  text-align: center;
  color: var(--text-muted);
  font-size: 0.875rem;
}

.proxy-row {
  margin-bottom: 0.75rem;
  padding: 0.5rem 0;
}

.proxy-label {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.proxy-select {
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  padding: 0.35rem 0.5rem;
}

.admin-log {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
}

.admin-log summary {
  cursor: pointer;
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}
</style>
