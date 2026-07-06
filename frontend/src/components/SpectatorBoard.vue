<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { POSITION_COLORS, POSITION_NAMES, POSITION_TO_LETTER } from '../constants'
import { phaseLabel } from '../auctionEngine'
import PlayerAvatar from './PlayerAvatar.vue'
import type {
  AuctionPhase,
  Captain,
  LiveBidEntry,
  OpenBidContext,
  Player,
  Position,
} from '../types'

const props = defineProps<{
  phase: AuctionPhase
  captains: Captain[]
  currentPool: Position | null
  currentPlayer: Player | null
  openBid: OpenBidContext | null
  poolOrder: Position[]
  isAdmin?: boolean
}>()

const secondsLeft = ref(0)
let tickTimer: ReturnType<typeof setInterval> | null = null

function updateTimer() {
  if (!props.openBid?.deadlineMs) {
    secondsLeft.value = 0
    return
  }
  secondsLeft.value = Math.max(0, (props.openBid.deadlineMs - Date.now()) / 1000)
}

watch(
  () => props.openBid?.deadlineMs,
  () => updateTimer(),
  { immediate: true },
)

onMounted(() => {
  tickTimer = setInterval(updateTimer, 200)
})

onUnmounted(() => {
  if (tickTimer) clearInterval(tickTimer)
})

const timerPct = computed(() => {
  if (!props.openBid) return 0
  const total = props.openBid.timeoutSeconds || 45
  return Math.min(100, (secondsLeft.value / total) * 100)
})

const timerLabel = computed(() => {
  if (!props.openBid) return ''
  return props.openBid.hasBids
    ? `${props.openBid.bidExtensionSeconds}s 内无人加价则落槌`
    : `${props.openBid.noBidTimeoutSeconds}s 内无人出价则流拍`
})

const timerUrgent = computed(() => secondsLeft.value > 0 && secondsLeft.value <= 8)

const captainAvatarMap = computed(() => {
  const map = new Map<string, string | null | undefined>()
  for (const c of props.captains) map.set(c.name, c.avatar)
  return map
})

const displayRows = computed(() => {
  if (props.openBid?.captainRows?.length) {
    return props.openBid.captainRows.map((row) => ({
      ...row,
      avatar: captainAvatarMap.value.get(row.name),
      position: props.currentPlayer?.position ?? props.currentPool,
    }))
  }
  return props.captains.map((c) => ({
    name: c.name,
    funds: c.funds,
    latestBid: null as number | null,
    isLeader: false,
    canBid: true,
    skipReason: null as string | null,
    passed: false,
    avatar: c.avatar,
    position: props.currentPool,
  }))
})

const liveBids = computed((): LiveBidEntry[] => props.openBid?.liveBids ?? [])

const spotlightPlayer = computed(() => props.openBid?.player ?? props.currentPlayer)

const leaderName = computed(() => props.openBid?.currentLeader)
const leaderPrice = computed(() => props.openBid?.currentPrice ?? 0)
const leaderCaptain = computed(() => props.openBid?.leaderCaptain)

function posLabel(position: Position | null | undefined) {
  if (!position) return '—'
  return `${POSITION_TO_LETTER[position]}·${POSITION_NAMES[position]}`
}
</script>

<template>
  <div class="spectator-board">
    <header class="board-header">
      <div class="header-brand">
        <img src="/logo.svg" alt="" class="brand-logo" />
        <div>
          <p class="brand-eyebrow">BAICAI CUP · LIVE AUCTION</p>
          <h1 class="brand-title">公开叫价 · 观战大屏</h1>
        </div>
      </div>
      <div class="header-meta">
        <span class="phase-badge">{{ phaseLabel(phase) }}</span>
        <span v-if="currentPool" class="pool-badge" :style="{ '--c': POSITION_COLORS[currentPool] }">
          {{ posLabel(currentPool) }}
        </span>
      </div>
    </header>

    <div class="board-grid">
      <!-- 左侧：队长实时出价 -->
      <section class="panel captains-panel card">
        <h2 class="panel-title">队长出价板</h2>
        <div class="captain-grid">
          <div
            v-for="row in displayRows"
            :key="row.name"
            class="captain-card"
            :class="{
              leader: row.isLeader,
              passed: row.passed,
              disabled: !row.canBid && !row.passed,
            }"
          >
            <PlayerAvatar
              :name="row.name"
              :avatar="row.avatar"
              :position="row.position ?? undefined"
              size="md"
            />
            <div class="captain-info">
              <span class="captain-name">{{ row.name }}</span>
              <span v-if="row.funds != null" class="captain-funds">余 {{ row.funds }}w</span>
            </div>
            <div class="captain-bid">
              <span v-if="row.passed" class="bid-pass">放弃</span>
              <span v-else-if="row.latestBid != null" class="bid-amt">{{ row.latestBid }}w</span>
              <span v-else-if="row.skipReason" class="bid-skip">{{ row.skipReason }}</span>
              <span v-else class="bid-wait">—</span>
            </div>
            <span v-if="row.isLeader" class="leader-crown">领先</span>
          </div>
        </div>

        <div v-if="liveBids.length" class="live-feed">
          <h3 class="feed-title">实时出价</h3>
          <ul class="feed-list">
            <li v-for="bid in liveBids" :key="bid.id" class="feed-item">
              <span class="feed-time">{{ bid.time }}</span>
              <span class="feed-cap">{{ bid.captain }}</span>
              <span class="feed-amt">{{ bid.amount }}w</span>
            </li>
          </ul>
        </div>
        <p v-else-if="phase === 'open_bid'" class="feed-empty">等待首次出价…</p>
      </section>

      <!-- 右侧：当前标的 + 最高价 -->
      <section class="panel lot-panel card">
        <template v-if="spotlightPlayer && phase === 'open_bid'">
          <p class="lot-eyebrow">当前拍卖标的</p>
          <div class="lot-spotlight">
            <div class="lot-player">
              <PlayerAvatar
                :name="spotlightPlayer.name"
                :serial="spotlightPlayer.serial"
                :avatar="spotlightPlayer.avatar"
                :position="spotlightPlayer.position"
                size="xl"
              />
              <p class="lot-serial">{{ spotlightPlayer.serial }}</p>
              <h2 class="lot-name">{{ spotlightPlayer.name }}</h2>
              <p class="lot-pos" :style="{ color: POSITION_COLORS[spotlightPlayer.position] }">
                {{ posLabel(spotlightPlayer.position) }}
              </p>
              <div class="lot-prices">
                <span>起拍 {{ openBid?.startPrice ?? spotlightPlayer.startPrice }}w</span>
                <span v-if="openBid?.buyoutPrice || spotlightPlayer.buyoutPrice">
                  一口价 {{ openBid?.buyoutPrice ?? spotlightPlayer.buyoutPrice }}w
                </span>
              </div>
            </div>

            <div class="lot-auction">
              <p class="timer-hint">{{ timerLabel }}</p>
              <div class="timer-ring" :class="{ urgent: timerUrgent }">
                <svg viewBox="0 0 120 120" class="timer-svg">
                  <circle cx="60" cy="60" r="52" class="timer-bg" />
                  <circle
                    cx="60"
                    cy="60"
                    r="52"
                    class="timer-fg"
                    :style="{ strokeDashoffset: `${326.7 * (1 - timerPct / 100)}` }"
                  />
                </svg>
                <div class="timer-text">
                  <span class="timer-num">{{ secondsLeft.toFixed(1) }}</span>
                  <span class="timer-unit">秒</span>
                </div>
              </div>

              <div class="current-price-block">
                <span class="price-label">当前最高价</span>
                <span class="price-value">{{ leaderPrice || openBid?.startPrice || '—' }}<small>w</small></span>
              </div>

              <div v-if="leaderName" class="leader-block">
                <span class="leader-label">领先队长</span>
                <div class="leader-row">
                  <PlayerAvatar
                    :name="leaderName"
                    :avatar="leaderCaptain?.avatar ?? captainAvatarMap.get(leaderName)"
                    :position="spotlightPlayer.position"
                    size="md"
                  />
                  <div>
                    <p class="leader-name">{{ leaderName }}</p>
                    <p class="leader-bid">{{ leaderPrice }}w</p>
                  </div>
                </div>
              </div>
              <p v-else class="no-bid">尚无人出价，等待队长叫价…</p>
            </div>
          </div>

          <div v-if="$slots.bidPanel" class="bid-panel-slot">
            <slot name="bidPanel" />
          </div>
        </template>

        <template v-else-if="phase === 'pool_select'">
          <div class="waiting-state">
            <span class="wait-icon">🎯</span>
            <h2>等待选择位置池</h2>
            <p>管理员正在选择下一个拍卖位置…</p>
            <div v-if="poolOrder.length" class="done-pools">
              <span v-for="(p, i) in poolOrder" :key="p + i" class="done-chip">
                {{ posLabel(p) }}
              </span>
            </div>
          </div>
        </template>

        <template v-else-if="phase === 'pool_draw'">
          <div class="waiting-state purple">
            <span class="wait-icon">?</span>
            <h2>抽取拍卖标的</h2>
            <p>即将揭晓本池选手…</p>
          </div>
        </template>

        <template v-else-if="phase === 'player_done'">
          <div class="waiting-state">
            <span class="wait-icon">⏳</span>
            <h2>准备下一位</h2>
            <p>即将抽取下一名选手…</p>
          </div>
        </template>

        <template v-else>
          <div class="waiting-state">
            <img src="/logo.svg" alt="" class="wait-logo" />
            <h2>选人仪式</h2>
            <p>公开叫价 · 倒计时落槌</p>
          </div>
        </template>
      </section>
    </div>
  </div>
</template>

<style scoped>
.spectator-board {
  width: 100%;
}

.board-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.brand-logo {
  width: 48px;
  height: 48px;
  filter: drop-shadow(0 0 12px rgba(168, 85, 247, 0.4));
}

.brand-eyebrow {
  font-family: var(--font-display);
  font-size: 0.65rem;
  letter-spacing: 0.14em;
  color: var(--purple);
}

.brand-title {
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 800;
  background: linear-gradient(135deg, #fff 20%, var(--purple), var(--gold-bright));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.phase-badge {
  font-size: 0.8125rem;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  background: rgba(168, 85, 247, 0.12);
  color: #c084fc;
  font-weight: 600;
}

.pool-badge {
  font-size: 0.8125rem;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--c) 14%, transparent);
  color: var(--c);
  border: 1px solid color-mix(in srgb, var(--c) 30%, transparent);
  font-weight: 600;
}

.board-grid {
  display: grid;
  grid-template-columns: 1fr 1.05fr;
  gap: 1rem;
  align-items: start;
}

@media (max-width: 960px) {
  .board-grid {
    grid-template-columns: 1fr;
  }
}

.panel {
  padding: 1rem 1.15rem;
  min-height: 420px;
}

.panel-title {
  font-family: var(--font-display);
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 0.85rem;
}

.captain-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.captain-card {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 0.65rem;
  padding: 0.55rem 0.65rem;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border);
  position: relative;
  transition: border-color 0.2s, background 0.2s;
}

.captain-card.leader {
  border-color: rgba(245, 197, 66, 0.45);
  background: rgba(245, 197, 66, 0.08);
}

.captain-card.passed,
.captain-card.disabled {
  opacity: 0.5;
}

.captain-info {
  min-width: 0;
}

.captain-name {
  display: block;
  font-weight: 700;
  font-size: 0.875rem;
}

.captain-funds {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.captain-bid {
  text-align: right;
}

.bid-amt {
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--gold);
}

.bid-pass {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.bid-skip {
  font-size: 0.72rem;
  color: var(--text-muted);
  max-width: 80px;
}

.bid-wait {
  color: var(--text-muted);
}

.leader-crown {
  position: absolute;
  top: -6px;
  right: 8px;
  font-size: 0.62rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 999px;
  background: var(--gold);
  color: #422006;
}

.live-feed {
  border-top: 1px solid var(--border);
  padding-top: 0.85rem;
}

.feed-title {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
  letter-spacing: 0.04em;
}

.feed-list {
  list-style: none;
  max-height: 180px;
  overflow-y: auto;
}

.feed-item {
  display: grid;
  grid-template-columns: 52px 1fr auto;
  gap: 0.5rem;
  padding: 0.35rem 0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.08);
  font-size: 0.8125rem;
  animation: feedIn 0.35s ease;
}

@keyframes feedIn {
  from { opacity: 0; transform: translateX(-8px); }
  to { opacity: 1; transform: translateX(0); }
}

.feed-time {
  color: var(--text-muted);
  font-size: 0.72rem;
}

.feed-amt {
  font-weight: 700;
  color: var(--gold);
  font-family: var(--font-display);
}

.feed-empty {
  font-size: 0.8125rem;
  color: var(--text-muted);
  text-align: center;
  padding: 1rem;
}

.lot-panel {
  border-color: rgba(245, 197, 66, 0.2);
}

.lot-eyebrow {
  font-size: 0.72rem;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

.lot-spotlight {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.lot-player {
  text-align: center;
}

.lot-serial {
  font-family: var(--font-display);
  font-size: 0.8125rem;
  color: var(--accent);
  margin-top: 0.75rem;
}

.lot-name {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 800;
  margin: 0.25rem 0;
}

.lot-pos {
  font-size: 0.9375rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.lot-prices {
  display: flex;
  justify-content: center;
  gap: 1rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.lot-auction {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}

.timer-ring {
  position: relative;
  width: 120px;
  height: 120px;
}

.timer-ring.urgent .timer-fg {
  stroke: var(--red);
}

.timer-ring.urgent .timer-num {
  color: var(--red);
}

.timer-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.timer-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.08);
  stroke-width: 8;
}

.timer-fg {
  fill: none;
  stroke: var(--gold);
  stroke-width: 8;
  stroke-linecap: round;
  stroke-dasharray: 326.7;
  transition: stroke-dashoffset 0.2s linear;
}

.timer-text {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.timer-num {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--gold);
  line-height: 1;
}

.timer-unit {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.current-price-block {
  text-align: center;
}

.price-label {
  display: block;
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}

.price-value {
  font-family: var(--font-display);
  font-size: 2.75rem;
  font-weight: 800;
  color: var(--gold);
  line-height: 1;
}

.price-value small {
  font-size: 1.25rem;
  opacity: 0.8;
}

.leader-block {
  width: 100%;
  padding: 0.75rem;
  background: rgba(245, 197, 66, 0.08);
  border-radius: 10px;
  border: 1px solid rgba(245, 197, 66, 0.25);
}

.leader-label {
  display: block;
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.leader-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.leader-name {
  font-weight: 700;
  font-size: 1rem;
  color: var(--green);
}

.leader-bid {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--gold);
}

.no-bid {
  font-size: 0.875rem;
  color: var(--text-muted);
  text-align: center;
}

.timer-hint {
  font-size: 0.72rem;
  color: var(--text-muted);
  text-align: center;
  margin-bottom: -0.25rem;
}

.bid-panel-slot {
  margin-top: 1rem;
  border-top: 1px solid var(--border);
  padding-top: 1rem;
}

.waiting-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 360px;
  text-align: center;
  gap: 0.5rem;
  color: var(--text-muted);
}

.waiting-state.purple .wait-icon {
  color: var(--purple);
}

.wait-icon {
  font-size: 2.5rem;
}

.waiting-state h2 {
  font-family: var(--font-display);
  font-size: 1.35rem;
  color: var(--text);
}

.wait-logo {
  width: 64px;
  opacity: 0.75;
}

.done-pools {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  justify-content: center;
  margin-top: 0.75rem;
}

.done-chip {
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
}
</style>
