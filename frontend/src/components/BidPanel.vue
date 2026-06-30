<script setup lang="ts">
import { computed } from 'vue'
import { MIN_INCREMENT, MAX_INCREMENT } from '../auctionEngine'
import type { BiddingContext } from '../types'

const props = defineProps<{
  bidding: BiddingContext | null
  canBid: boolean
  proxyMode?: boolean
  waitingLabel?: string
}>()

const emit = defineEmits<{
  bid: [increment: number]
  buyout: []
  pass: []
}>()

const minInc = computed(() =>
  Math.max(props.bidding?.lastIncrement ?? MIN_INCREMENT, MIN_INCREMENT),
)

const nextPrice = computed(() => {
  if (!props.bidding) return 0
  return Math.min(
    props.bidding.currentPrice + minInc.value,
    props.bidding.player.buyoutPrice,
  )
})

const canBuyout = computed(() => {
  if (!props.bidding) return false
  return (
    props.bidding.isFirstRound &&
    props.bidding.turnCaptain.funds >= props.bidding.player.buyoutPrice
  )
})
</script>

<template>
  <div v-if="bidding && canBid" class="bid-panel card my-turn">
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
        <strong>{{ bidding.highestBidder ?? '暂无' }}</strong>
      </div>
      <div class="info-row">
        <span>最低加价</span>
        <strong>{{ minInc }}w</strong>
      </div>
      <div class="info-row">
        <span>下一口价</span>
        <strong class="gold">{{ nextPrice }}w</strong>
      </div>
      <div class="info-row">
        <span>剩余资金</span>
        <strong>{{ bidding.turnCaptain.funds }}w</strong>
      </div>
    </div>
    <div class="bid-actions">
      <button class="btn-primary" @click="emit('bid', minInc)">
        加价 +{{ minInc }}w
      </button>
      <button v-if="canBuyout" class="btn-gold" @click="emit('buyout')">
        一口价 {{ bidding.player.buyoutPrice }}w
      </button>
      <button class="btn-ghost" @click="emit('pass')">放弃</button>
    </div>
    <div class="inc-presets">
      <span class="preset-label">快捷加价：</span>
      <button
        v-for="inc in [10, 20, 50, 100].filter((n) => n >= minInc && n <= MAX_INCREMENT)"
        :key="inc"
        class="btn-ghost preset-btn"
        @click="emit('bid', inc)"
      >
        +{{ inc }}w
      </button>
    </div>
  </div>
  <div v-else-if="bidding" class="bid-panel card wait-hint">
    <span class="pulse" />
    {{ waitingLabel || `${bidding.turnCaptain.name} 的回合` }}
  </div>
</template>

<style scoped>
.panel-title {
  font-size: 1rem;
  margin-bottom: 0.75rem;
  color: var(--gold);
}

.my-turn {
  border-color: var(--gold);
  box-shadow: 0 0 24px var(--gold-dim);
}

.bid-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
  margin-bottom: 1rem;
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
  font-size: 1rem;
}

.info-row .gold {
  color: var(--gold);
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
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

.wait-hint {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--text-muted);
  font-size: 0.875rem;
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
