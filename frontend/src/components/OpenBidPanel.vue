<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { POSITION_NAMES } from '../constants'
import { quickIncrements } from '../auctionEngine'
import { playSound, unlockAudio } from '../lib/soundEngine'
import type { Captain, OpenBidContext } from '../types'

const props = defineProps<{
  openBid: OpenBidContext
  canSubmit: boolean
  hasPassed: boolean
  proxyMode?: boolean
  proxyCaptainName?: string | null
  selfCaptainName?: string | null
  isAdmin?: boolean
}>()

const emit = defineEmits<{
  bid: [amount: number]
  pass: []
  buyout: []
}>()

const bidInput = ref('')
const localError = ref('')

const player = computed(() => props.openBid.player)

const activeRow = computed(() => {
  if (props.proxyMode && props.proxyCaptainName) {
    return props.openBid.captainRows.find((r) => r.name === props.proxyCaptainName) ?? null
  }
  if (props.selfCaptainName) {
    return props.openBid.captainRows.find((r) => r.name === props.selfCaptainName) ?? null
  }
  return props.openBid.captainRows.find((r) => r.canBid && !r.passed) ?? null
})

const activeCaptain = computed((): Captain | null => {
  if (!props.proxyMode || !props.proxyCaptainName) return null
  return (
    props.openBid.eligibleCaptains.find((c) => c.name === props.proxyCaptainName) ?? null
  )
})

const maxFunds = computed(() => {
  if (activeRow.value?.funds != null) return activeRow.value.funds
  if (props.proxyMode && activeCaptain.value) return activeCaptain.value.funds
  return 0
})

const canBuyout = computed(() => activeRow.value?.canBuyout ?? false)
const buyoutUsed = computed(() => activeRow.value?.buyoutUsed ?? false)

const quickBtns = computed(() =>
  quickIncrements(props.openBid.currentPrice, props.openBid.minNextBid),
)

watch(
  () => props.openBid.minNextBid,
  (v) => {
    bidInput.value = String(v)
    localError.value = ''
  },
  { immediate: true },
)

function parseAmount(): number | null {
  const n = Number(bidInput.value.trim())
  if (!Number.isFinite(n) || n <= 0) return null
  return Math.round(n)
}

function validate(amount: number): string | null {
  if (amount < props.openBid.minNextBid) return `须 ≥ ${props.openBid.minNextBid}w`
  if (amount > maxFunds.value) return `超出剩余资金 ${maxFunds.value}w`
  return null
}

function submit(amount: number) {
  localError.value = ''
  const err = validate(amount)
  if (err) {
    localError.value = err
    playSound('uiError')
    return
  }
  void unlockAudio()
  playSound('uiClick')
  emit('bid', amount)
}

function onSubmit() {
  const amount = parseAmount()
  if (amount == null) {
    localError.value = '请输入有效出价'
    playSound('uiError')
    return
  }
  submit(amount)
}

function onQuickBid(amount: number) {
  void unlockAudio()
  playSound('uiClick')
  submit(amount)
}

function onBuyout() {
  void unlockAudio()
  playSound('uiClick')
  emit('buyout')
}

function onPass() {
  void unlockAudio()
  playSound('uiClick')
  emit('pass')
}
</script>

<template>
  <div class="open-bid-panel card">
    <div class="panel-header">
      <h3 class="panel-title">
        <template v-if="proxyMode">代 {{ proxyCaptainName }} 出价</template>
        <template v-else>公开叫价</template>
      </h3>
      <span v-if="hasPassed" class="passed-tag">已放弃本轮</span>
      <span v-else-if="!canSubmit" class="wait-tag">暂不可出价</span>
    </div>

    <p class="panel-hint">
      {{ POSITION_NAMES[player.position] }} · 当前价
      <strong>{{ openBid.currentPrice || openBid.startPrice }}w</strong>
      · 最低加价 {{ openBid.minIncrement }}w
      <template v-if="openBid.buyoutPrice"> · 一口价 {{ openBid.buyoutPrice }}w</template>
      <template v-if="buyoutUsed"> · <span class="buyout-used">已使用一口价机会</span></template>
    </p>

    <div v-if="canSubmit && !hasPassed" class="bid-controls">
      <div class="quick-row">
        <button
          v-for="amt in quickBtns"
          :key="amt"
          class="btn-ghost btn-quick"
          @click="onQuickBid(amt)"
        >
          {{ amt }}w
        </button>
        <button
          v-if="openBid.buyoutPrice && canBuyout"
          class="btn-primary btn-buyout"
          @click="onBuyout"
        >
          一口价 {{ openBid.buyoutPrice }}w
        </button>
      </div>
      <div class="input-row">
        <input
          v-model="bidInput"
          type="number"
          class="bid-input"
          :min="openBid.minNextBid"
          @keyup.enter="onSubmit"
        />
        <span class="unit">w</span>
        <button class="btn-primary" @click="onSubmit">出价</button>
        <button class="btn-ghost" @click="onPass">放弃</button>
      </div>
      <p v-if="localError" class="local-error">{{ localError }}</p>
    </div>
  </div>
</template>

<style scoped>
.open-bid-panel {
  padding: 1rem 1.15rem;
  border-color: rgba(245, 197, 66, 0.25);
  background: linear-gradient(160deg, rgba(14, 20, 32, 0.95), rgba(8, 12, 20, 0.9));
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 0.5rem;
}

.panel-title {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--gold);
}

.passed-tag,
.wait-tag {
  font-size: 0.72rem;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-muted);
}

.panel-hint {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin-bottom: 0.85rem;
}

.panel-hint strong {
  color: var(--gold);
}

.buyout-used {
  color: var(--text-muted);
}

.quick-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.65rem;
}

.btn-quick {
  font-family: var(--font-display);
  font-weight: 700;
  min-width: 72px;
}

.btn-buyout {
  background: linear-gradient(135deg, #d97706, #b45309);
}

.input-row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.bid-input {
  width: 100px;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  padding: 0.45rem 0.55rem;
  font-size: 1rem;
  font-weight: 700;
  font-family: var(--font-display);
}

.unit {
  color: var(--text-muted);
  font-size: 0.875rem;
}

.local-error {
  margin-top: 0.5rem;
  font-size: 0.8125rem;
  color: var(--red);
}
</style>
