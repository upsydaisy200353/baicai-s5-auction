<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import PoolPickPanel from './PoolPickPanel.vue'
import { phaseLabel } from '../auctionEngine'
import { playSound, unlockAudio } from '../lib/soundEngine'
import type { AuctionPhase, AuctionSettings, Position } from '../types'

const props = defineProps<{
  phase: AuctionPhase
  availablePools: Position[]
  poolOrder: Position[]
  canHammer: boolean
  auctionSettings?: AuctionSettings
}>()

const emit = defineEmits<{
  selectPool: [pool: Position]
  hammer: []
  reset: []
  updateSettings: [settings: AuctionSettings]
}>()

const showPoolPick = computed(() => props.phase === 'pool_select')
const showSettings = ref(false)
const bidExtension = ref(45)
const noBidTimeout = ref(60)

watch(
  () => props.auctionSettings,
  (s) => {
    if (!s) return
    bidExtension.value = s.bidExtensionSeconds
    noBidTimeout.value = s.noBidTimeoutSeconds
  },
  { immediate: true },
)

function applySettings() {
  void unlockAudio()
  playSound('uiClick')
  emit('updateSettings', {
    bidExtensionSeconds: bidExtension.value,
    noBidTimeoutSeconds: noBidTimeout.value,
  })
  showSettings.value = false
}

function onHammer() {
  void unlockAudio()
  emit('hammer')
}

function onReset() {
  void unlockAudio()
  playSound('uiClick')
  emit('reset')
}
</script>

<template>
  <div class="admin-bar card">
    <div class="bar-left">
      <span class="bar-label">管理员</span>
      <span class="phase-pill">{{ phaseLabel(phase) }}</span>
    </div>
    <div class="bar-actions">
      <button class="btn-ghost" @click="showSettings = !showSettings">计时设置</button>
      <button
        v-if="canHammer"
        class="btn-primary btn-hammer"
        @click="onHammer"
      >
        落槌
      </button>
      <button class="btn-ghost" @click="onReset">重置仪式</button>
    </div>
  </div>

  <div v-if="showSettings" class="settings-panel card">
    <h3 class="settings-title">拍卖计时</h3>
    <div class="settings-row">
      <label>
        加价后倒计时（秒）
        <input v-model.number="bidExtension" type="number" min="5" max="300" />
      </label>
      <label>
        无人出价流拍（秒）
        <input v-model.number="noBidTimeout" type="number" min="10" max="600" />
      </label>
      <button class="btn-primary" @click="applySettings">保存</button>
    </div>
    <p class="settings-hint">有人出价后，{{ bidExtension }}s 内无人继续加价则最高价者得；全程无人出价超过 {{ noBidTimeout }}s 则流拍。</p>
  </div>

  <PoolPickPanel
    v-if="showPoolPick"
    :available-pools="availablePools"
    :pool-order="poolOrder"
    @select="emit('selectPool', $event)"
  />
</template>

<style scoped>
.admin-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  border-color: rgba(168, 85, 247, 0.25);
}

.bar-left {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.bar-label {
  font-family: var(--font-display);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--purple);
  text-transform: uppercase;
}

.phase-pill {
  font-size: 0.8125rem;
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  background: rgba(168, 85, 247, 0.12);
  color: #c084fc;
}

.bar-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.btn-hammer {
  background: linear-gradient(135deg, #d97706, #b45309);
}

.settings-panel {
  padding: 0.85rem 1rem;
  margin-bottom: 1rem;
  border-color: rgba(168, 85, 247, 0.2);
}

.settings-title {
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--purple);
  margin-bottom: 0.65rem;
}

.settings-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: flex-end;
}

.settings-row label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.settings-row input {
  width: 120px;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  padding: 0.35rem 0.5rem;
}

.settings-hint {
  margin-top: 0.5rem;
  font-size: 0.72rem;
  color: var(--text-muted);
}
</style>
