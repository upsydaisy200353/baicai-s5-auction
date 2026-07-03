<script setup lang="ts">
import { computed } from 'vue'
import PoolPickPanel from './PoolPickPanel.vue'
import { phaseLabel } from '../auctionEngine'
import type { AuctionPhase, Position } from '../types'

const props = defineProps<{
  phase: AuctionPhase
  availablePools: Position[]
  poolOrder: Position[]
  canHammer: boolean
}>()

const emit = defineEmits<{
  selectPool: [pool: Position]
  hammer: []
  reset: []
}>()

const showPoolPick = computed(() => props.phase === 'pool_select')
</script>

<template>
  <div class="admin-bar card">
    <div class="bar-left">
      <span class="bar-label">管理员</span>
      <span class="phase-pill">{{ phaseLabel(phase) }}</span>
    </div>
    <div class="bar-actions">
      <button
        v-if="canHammer"
        class="btn-primary btn-hammer"
        @click="emit('hammer')"
      >
        落槌
      </button>
      <button class="btn-ghost" @click="emit('reset')">重置仪式</button>
    </div>
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
</style>
