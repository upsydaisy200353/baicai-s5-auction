<script setup lang="ts">
import { CEREMONY_STEPS } from '../auctionEngine'
import type { AuctionPhase } from '../types'

defineProps<{ phase: AuctionPhase }>()

const stepPhaseMap: Record<string, AuctionPhase[]> = {
  intro: ['intro'],
  pool_select: ['pool_select'],
  bid_order_select: ['bid_order_select'],
  pool_announce: ['pool_announce'],
  pool_draw: ['pool_draw'],
  bidding: ['bidding'],
  winner_reveal: ['winner_reveal', 'player_done'],
  finished: ['finished'],
}

function isActive(stepId: string, phase: AuctionPhase) {
  return stepPhaseMap[stepId]?.includes(phase)
}

function isDone(stepId: string, phase: AuctionPhase) {
  const order = CEREMONY_STEPS.map((s) => s.id)
  const curIdx = order.findIndex((id) => stepPhaseMap[id]?.includes(phase))
  const stepIdx = order.indexOf(stepId as (typeof order)[number])
  if (phase === 'idle') return false
  if (phase === 'finished') return true
  return curIdx > stepIdx
}
</script>

<template>
  <div v-if="phase !== 'idle'" class="timeline card">
    <div
      v-for="(step, i) in CEREMONY_STEPS"
      :key="step.id"
      class="step"
      :class="{
        active: isActive(step.id, phase),
        done: isDone(step.id, phase),
      }"
    >
      <div class="step-dot">{{ i + 1 }}</div>
      <span class="step-label">{{ step.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.timeline {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 0.5rem;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
}

.step {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  opacity: 0.5;
}

.step.active {
  opacity: 1;
  color: var(--gold);
}

.step.done {
  opacity: 0.85;
  color: var(--green);
}

.step-dot {
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  background: var(--bg-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.65rem;
  font-weight: 700;
  flex-shrink: 0;
}

.step.active .step-dot {
  background: var(--gold);
  color: #1a1a1a;
  box-shadow: 0 0 12px var(--gold-dim);
}

.step.done .step-dot {
  background: var(--green-dim);
  color: var(--green);
}
</style>
