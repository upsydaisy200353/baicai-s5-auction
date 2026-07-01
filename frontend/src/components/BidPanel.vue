<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { MAX_INCREMENT } from '../auctionEngine'
import PlayerAvatar from './PlayerAvatar.vue'
import type { BiddingContext } from '../types'

const props = defineProps<{
  bidding: BiddingContext | null
  canBid: boolean
  proxyMode?: boolean
  waitingLabel?: string
}>()

const emit = defineEmits<{
  bid: [amount: number]
  bidIncrement: [increment: number]
  buyout: []
  pass: []
}>()

const bidInput = ref('')
const localError = ref('')

const minNextBid = computed(() => props.bidding?.minNextBid ?? 0)
const minRaise = computed(() => props.bidding?.minRaise ?? 10)
const buyoutPrice = computed(() => props.bidding?.player.buyoutPrice ?? 0)
const maxBid = computed(() => {
  if (!props.bidding) return 0
  return Math.min(props.bidding.turnCaptain.funds, buyoutPrice.value)
})

watch(
  () => props.bidding?.turnCaptain.name,
  () => {
    localError.value = ''
    if (props.bidding) {
      bidInput.value = String(props.bidding.minNextBid)
    }
  },
  { immediate: true },
)

watch(
  () => props.bidding?.minNextBid,
  (v) => {
    if (v != null && props.canBid) bidInput.value = String(v)
  },
)

const canBuyout = computed(() => {
  if (!props.bidding) return false
  return (
    props.bidding.isFirstRound &&
    props.bidding.turnCaptain.funds >= props.bidding.player.buyoutPrice
  )
})

function parseAmount(): number | null {
  const n = Number(bidInput.value.trim())
  if (!Number.isFinite(n) || n <= 0) return null
  return Math.round(n)
}

function validateLocal(amount: number): string | null {
  if (amount % 10 !== 0) return '出价须为 10 的倍数'
  if (amount > maxBid.value) return `不能超过 ${maxBid.value}w（资金/一口价上限）`
  if (amount < minNextBid.value) return `最低出价 ${minNextBid.value}w`
  return null
}

function onSubmitBid() {
  localError.value = ''
  const amount = parseAmount()
  if (amount == null) {
    localError.value = '请输入有效出价'
    return
  }
  const err = validateLocal(amount)
  if (err) {
    localError.value = err
    return
  }
  emit('bid', amount)
}

function onQuickIncrement(inc: number) {
  localError.value = ''
  if (!props.bidding) return
  const target = props.bidding.currentPrice + inc
  bidInput.value = String(Math.min(target, maxBid.value))
  emit('bidIncrement', inc)
}
</script>

<template>
  <div v-if="bidding && canBid" class="bid-panel card my-turn">
    <img src="/images/auction-accent.png" alt="" class="bid-accent" aria-hidden="true" />
    <div class="bid-player">
      <PlayerAvatar
        :name="bidding.player.name"
        :serial="bidding.player.serial"
        :avatar="bidding.player.avatar"
        :position="bidding.player.position"
        size="md"
      />
      <div>
        <p class="bid-player-name">{{ bidding.player.name }}</p>
        <p class="bid-player-serial">{{ bidding.player.serial }}</p>
      </div>
    </div>
    <h3 class="panel-title">
      <template v-if="proxyMode">代 {{ bidding.turnCaptain.name }} 出价（模拟）</template>
      <template v-else>轮到你出价 — {{ bidding.turnCaptain.name }}</template>
    </h3>
    <div class="bid-info">
      <div class="info-row">
        <span>当前价</span>
        <strong>{{ bidding.currentPrice }}w</strong>
      </div>
      <div class="info-row">
        <span>最高出价</span>
        <strong>{{ bidding.highestBidder ?? '暂无（起拍中）' }}</strong>
      </div>
      <div class="info-row">
        <span>最低出价</span>
        <strong class="gold">{{ minNextBid }}w</strong>
      </div>
      <div class="info-row">
        <span>加价幅度</span>
        <strong>≥ {{ minRaise }}w · 须为 10 的倍数</strong>
      </div>
      <div class="info-row">
        <span>剩余资金</span>
        <strong>{{ bidding.turnCaptain.funds }}w</strong>
      </div>
      <div class="info-row">
        <span>一口价</span>
        <strong>{{ buyoutPrice }}w</strong>
      </div>
    </div>

    <div class="bid-input-row">
      <label class="bid-label">
        出价（w）
        <input
          v-model="bidInput"
          type="number"
          min="10"
          step="10"
          :max="maxBid"
          class="bid-input"
          @keyup.enter="onSubmitBid"
        />
      </label>
      <button class="btn-primary bid-submit" type="button" @click="onSubmitBid">
        出价
      </button>
    </div>
    <p v-if="localError" class="local-error">{{ localError }}</p>

    <div class="bid-actions">
      <button v-if="canBuyout" class="btn-gold" type="button" @click="emit('buyout')">
        一口价 {{ bidding.player.buyoutPrice }}w
      </button>
      <button class="btn-ghost" type="button" @click="emit('pass')">
        放弃（退出本场）
      </button>
    </div>
    <div class="inc-presets">
      <span class="preset-label">快捷加价：</span>
      <button
        v-for="inc in [10, 20, 50, 100].filter((n) => n >= minRaise && n <= MAX_INCREMENT)"
        :key="inc"
        type="button"
        class="btn-ghost preset-btn"
        @click="onQuickIncrement(inc)"
      >
        +{{ inc }}w
      </button>
    </div>
    <p v-if="bidding.passedCaptains.length" class="passed-hint">
      已放弃本场：{{ bidding.passedCaptains.join('、') }}
    </p>
  </div>
  <div v-else-if="bidding" class="bid-panel card wait-hint">
    <span class="pulse" />
    {{ waitingLabel || `${bidding.turnCaptain.name} 的回合` }}
    <span v-if="bidding.passedCaptains.length" class="passed-mini">
      · 已退出：{{ bidding.passedCaptains.length }} 人
    </span>
  </div>
</template>

<style scoped>
.bid-player {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
  padding-bottom: 0.85rem;
  border-bottom: 1px solid var(--border);
}

.bid-player-name {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 1rem;
}

.bid-player-serial {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.panel-title {
  font-family: var(--font-display);
  font-size: 1rem;
  margin-bottom: 0.85rem;
  color: var(--gold);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.panel-title::before {
  content: '🔨';
  font-size: 0.9rem;
}

.my-turn {
  border-color: rgba(245, 197, 66, 0.4);
  box-shadow: var(--shadow-card), 0 0 32px rgba(245, 197, 66, 0.12);
  animation: fadeUp 0.35s ease;
  position: relative;
  overflow: hidden;
}

.bid-accent {
  position: absolute;
  right: -6%;
  top: -12%;
  width: 140px;
  opacity: 0.12;
  pointer-events: none;
  transform: rotate(8deg);
}

.bid-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.55rem;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}

.info-row {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  font-size: 0.8125rem;
}

.info-row span {
  color: var(--text-muted);
}

.info-row strong {
  font-size: 0.9375rem;
}

.info-row .gold {
  color: var(--gold);
}

.bid-input-row {
  display: flex;
  gap: 0.5rem;
  align-items: flex-end;
  margin-bottom: 0.5rem;
}

.bid-label {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.bid-input {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.6rem 0.85rem;
  color: var(--text);
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 700;
  width: 100%;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.bid-input:focus {
  outline: none;
  border-color: rgba(245, 197, 66, 0.45);
  box-shadow: 0 0 0 3px rgba(245, 197, 66, 0.1);
}

.bid-submit {
  padding: 0.55rem 1.25rem;
  flex-shrink: 0;
}

.local-error {
  color: var(--red);
  font-size: 0.8125rem;
  margin-bottom: 0.5rem;
}

.bid-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.inc-presets {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.preset-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.preset-btn {
  padding: 0.3rem 0.6rem;
  font-size: 0.75rem;
  border-radius: 999px;
}

.passed-hint {
  margin-top: 0.75rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.wait-hint {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--text-muted);
  font-size: 0.875rem;
  flex-wrap: wrap;
  padding: 1rem 1.15rem;
  background: rgba(0, 0, 0, 0.15);
  border-radius: var(--radius-sm);
}

.passed-mini {
  font-size: 0.75rem;
  opacity: 0.8;
}

.pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
}
</style>
