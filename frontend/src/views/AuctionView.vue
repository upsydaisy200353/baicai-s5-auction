<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import {
  beginCeremony,
  confirmBidPrep,
  confirmPool,
  confirmWinner,
  fetchAuctionState,
  revealDraw,
  resetAuction as apiResetAuction,
  setBidOrder,
  setPoolOrder,
  startAuction,
  submitBid,
  type ServerAuctionState,
} from '../api/auction'
import { fetchRoster } from '../api/roster'
import CaptainCards from '../components/CaptainCards.vue'
import PlayerTable from '../components/PlayerTable.vue'
import LogPanel from '../components/LogPanel.vue'
import BidPanel from '../components/BidPanel.vue'
import AuctionStage from '../components/AuctionStage.vue'
import CeremonyTimeline from '../components/CeremonyTimeline.vue'
import CeremonyOverlay from '../components/CeremonyOverlay.vue'
import PoolOrderPanel from '../components/PoolOrderPanel.vue'
import BidOrderPanel from '../components/BidOrderPanel.vue'
import { buildRosterRowsFromEntries, captainCanBidForPosition, captainSkipReason } from '../rosterUtils'
import { POSITION_NAMES } from '../constants'
import { useAuth } from '../stores/auth'
import type { Position, RosterEntry, RosterRow } from '../types'

const { isAdmin, isCaptain, captainName, user } = useAuth()

const state = ref<ServerAuctionState | null>(null)
const entries = ref<RosterEntry[]>([])
const loading = ref(true)
const error = ref('')
const actionMsg = ref('')
let pollTimer: ReturnType<typeof setInterval> | null = null

const overlayPhases = ['intro', 'pool_announce', 'pool_draw', 'winner_reveal', 'finished']

const activeCaptainName = computed(
  () => state.value?.bidding?.turnCaptain.name ?? null,
)

const isMyTurn = computed(() => {
  if (!state.value?.bidding) return false
  if (isAdmin.value) return true
  if (!isCaptain.value) return false
  return state.value.bidding.turnCaptain.name === captainName.value
})

const isProxyBid = computed(() => isAdmin.value && !!state.value?.bidding)

const proxyCaptainName = computed(
  () => state.value?.bidding?.turnCaptain.name,
)

const bidContextPosition = computed((): Position | null => {
  if (state.value?.bidding?.player.position) return state.value.bidding.player.position
  if (state.value?.currentPlayer?.position) return state.value.currentPlayer.position
  if (state.value?.currentPool) return state.value.currentPool
  return null
})

const ineligibleCaptainNames = computed((): string[] => {
  if (!state.value || !bidContextPosition.value) return []
  const pos = bidContextPosition.value
  return state.value.captains
    .filter((c) => !captainCanBidForPosition(c, pos, state.value!.players))
    .map((c) => c.name)
})

const ineligibleReasons = computed((): Record<string, string> => {
  const map: Record<string, string> = {}
  if (!state.value || !bidContextPosition.value) return map
  const pos = bidContextPosition.value
  for (const c of state.value.captains) {
    const reason = captainSkipReason(c, pos, state.value.players)
    if (reason) map[c.name] = reason
  }
  return map
})

const currentPoolLabel = computed(() => {
  if (!state.value?.currentPool) return ''
  const idx = state.value.currentPoolIndex + 1
  const total = state.value.poolOrder.length || 5
  return `${POSITION_NAMES[state.value.currentPool]} · 第 ${idx}/${total} 池`
})

const rosterRows = computed((): RosterRow[] => {
  if (!state.value) return buildRosterRowsFromEntries(entries.value)
  const playerMap = new Map(state.value.players.map((p) => [p.serial, p]))
  const captainMap = new Map(state.value.captains.map((c) => [c.name, c]))
  return buildRosterRowsFromEntries(entries.value).map((row) => {
    if (row.kind === 'player') {
      const live = playerMap.get(row.data.serial)
      return live ? { kind: 'player' as const, data: live } : row
    }
    const live = captainMap.get(row.data.name)
    return live
      ? { kind: 'captain' as const, data: { ...live, poolLetter: row.data.poolLetter } }
      : row
  })
})

async function refresh() {
  try {
    const [auctionState, roster] = await Promise.all([
      fetchAuctionState(),
      fetchRoster(),
    ])
    state.value = auctionState
    entries.value = roster.entries
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
  pollTimer = setInterval(refresh, 1500)
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

async function onSetPoolOrder(order: Position[]) {
  await runAction(() => setPoolOrder(order))
}

async function onSetBidOrder(names: string[]) {
  await runAction(() => setBidOrder(names), '出价顺序已保存')
}

async function onConfirmBidPrep(names: string[]) {
  await runAction(() => confirmBidPrep(names), '开始抽签')
}

async function onConfirmPool() {
  await runAction(confirmPool)
}

async function onRevealDraw() {
  await runAction(revealDraw)
}

async function onConfirmWinner() {
  await runAction(confirmWinner)
}

async function onReset() {
  await runAction(apiResetAuction, '已重置')
}

async function onBid(amount: number) {
  await runAction(() =>
    submitBid('bid', {
      amount,
      captainName: isAdmin.value ? proxyCaptainName.value : undefined,
    }),
  )
}

async function onBidIncrement(increment: number) {
  await runAction(() =>
    submitBid('bid', {
      increment,
      captainName: isAdmin.value ? proxyCaptainName.value : undefined,
    }),
  )
}

async function onBuyout() {
  await runAction(() =>
    submitBid('buyout', { captainName: isAdmin.value ? proxyCaptainName.value : undefined }),
  )
}

async function onPass() {
  await runAction(() =>
    submitBid('pass', { captainName: isAdmin.value ? proxyCaptainName.value : undefined }),
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
        @begin="onBegin"
        @confirm-pool="onConfirmPool"
        @reveal-draw="onRevealDraw"
        @confirm-winner="onConfirmWinner"
      />

      <header class="header">
        <div class="header-left">
          <h1 class="title">白菜杯 S5 选人仪式</h1>
          <p class="subtitle">
            已登录：<strong>{{ user?.displayName }}</strong>
            <span class="role-tag">{{ isAdmin ? '管理员' : '队长' }}</span>
            <span v-if="isAdmin" class="sim-tag">可代队长操作</span>
            · 多人同步拍卖
          </p>
        </div>
        <div class="header-actions">
          <template v-if="isAdmin">
            <button
              class="btn-primary"
              :disabled="state.phase !== 'idle' && state.phase !== 'finished'"
              @click="onStart"
            >
              开始仪式
            </button>
            <button class="btn-ghost" @click="onReset">重置</button>
          </template>
          <button class="btn-ghost" @click="refresh">刷新</button>
        </div>
      </header>

      <CeremonyTimeline :phase="state.phase" />

      <!-- 仪式配置：位置池 + 队长顺序 -->
      <div v-if="state.phase === 'pool_select' && isAdmin" class="setup-section">
        <PoolOrderPanel @confirm="onSetPoolOrder" />
        <BidOrderPanel
          :captains="state.captains"
          :saved-order="state.bidOrder"
          pool-label="首场预备"
          confirm-label="暂存出价顺序"
          @confirm="onSetBidOrder"
        />
      </div>

      <div v-else-if="state.phase === 'pool_select'" class="banner info">
        等待管理员设定位置池与出价顺序…
      </div>

      <BidOrderPanel
        v-else-if="state.phase === 'bid_order_select' && isAdmin"
        :captains="state.captains"
        :saved-order="state.bidOrder"
        :pool-label="currentPoolLabel"
        confirm-label="确认顺序并开始抽签"
        @confirm="onConfirmBidPrep"
      />

      <div v-else-if="state.phase === 'bid_order_select'" class="banner info">
        等待管理员设定【{{ state.currentPool ? POSITION_NAMES[state.currentPool] : '' }}】池出价顺序…
      </div>

      <div class="main-grid">
        <div class="left-col">
          <AuctionStage
            :phase="state.phase"
            :current-player="state.currentPlayer"
            :current-pool="state.currentPool"
            :pool-order="state.poolOrder"
          />

          <BidPanel
            v-if="state.phase === 'bidding'"
            :bidding="state.bidding"
            :can-bid="isMyTurn"
            :proxy-mode="isProxyBid"
            :waiting-label="
              !isMyTurn && state.bidding && !isAdmin
                ? `等待 ${state.bidding.turnCaptain.name} 出价…`
                : undefined
            "
            @bid="onBid"
            @bid-increment="onBidIncrement"
            @buyout="onBuyout"
            @pass="onPass"
          />

          <section class="section">
            <h3 class="section-title">队长</h3>
            <CaptainCards
              :captains="state.captains"
              :active-name="activeCaptainName"
              :current-position="bidContextPosition"
              :players="state.players"
              :ineligible-names="ineligibleCaptainNames"
              :ineligible-reasons="ineligibleReasons"
            />
          </section>
        </div>

        <div class="right-col">
          <LogPanel :logs="state.logs" />
          <section class="section">
            <h3 class="section-title">选手名单</h3>
            <PlayerTable
              :rows="rosterRows"
              :current-pool="state.currentPool"
              :highlight-serial="state.currentPlayer?.serial ?? state.lastResult?.player.serial ?? null"
            />
          </section>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.auction-view {
  width: 100%;
}

.banner {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.banner.info {
  background: rgba(59, 130, 246, 0.1);
  color: #93c5fd;
}

.banner.error {
  background: var(--red-dim);
  color: var(--red);
}

.banner.warn {
  background: var(--gold-dim);
  color: var(--gold);
}

.header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.title {
  font-size: 1.5rem;
  font-weight: 800;
  background: linear-gradient(90deg, var(--gold), #fde68a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin-top: 0.15rem;
}

.role-tag {
  display: inline-block;
  margin-left: 0.35rem;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: var(--accent-glow);
  color: var(--accent);
  font-size: 0.7rem;
}

.sim-tag {
  display: inline-block;
  margin-left: 0.25rem;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: var(--gold-dim);
  color: var(--gold);
  font-size: 0.7rem;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.pool-select {
  margin-bottom: 1rem;
}

.setup-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

@media (max-width: 960px) {
  .setup-section {
    grid-template-columns: 1fr;
  }
}

.main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

@media (max-width: 960px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
}

.left-col,
.right-col {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-title {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
  font-weight: 600;
}
</style>
