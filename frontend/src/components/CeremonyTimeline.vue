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
  <div v-if="phase !== 'idle'" class="timeline card fade-in">
    <div class="timeline-track">
      <div
        v-for="(step, i) in CEREMONY_STEPS"
        :key="step.id"
        class="step"
        :class="{
          active: isActive(step.id, phase),
          done: isDone(step.id, phase),
        }"
        :style="{ '--step-i': i }"
      >
        <div class="step-connector" v-if="i > 0" />
        <div class="step-dot">
          <span v-if="isDone(step.id, phase)" class="check">✓</span>
          <span v-else>{{ i + 1 }}</span>
        </div>
        <span class="step-label">{{ step.label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timeline {
  padding: 0.85rem 1.1rem;
  margin-bottom: 1.25rem;
  overflow-x: auto;
}

.timeline-track {
  display: flex;
  align-items: flex-start;
  gap: 0;
  min-width: max-content;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.45rem;
  min-width: 88px;
  position: relative;
  opacity: 0.42;
  transition: opacity 0.3s ease;
}

.step.active {
  opacity: 1;
}

.step.done {
  opacity: 0.88;
}

.step-connector {
  position: absolute;
  top: 14px;
  right: calc(50% + 16px);
  width: calc(100% - 32px);
  height: 2px;
  background: var(--border);
  transform: translateX(-50%);
}

.step.done .step-connector {
  background: linear-gradient(90deg, var(--cabbage), rgba(74, 222, 128, 0.3));
}

.step-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.04);
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-size: 0.7rem;
  font-weight: 700;
  flex-shrink: 0;
  transition: all 0.3s ease;
  z-index: 1;
}

.step.active .step-dot {
  background: linear-gradient(135deg, var(--gold), #d97706);
  border-color: var(--gold);
  color: #422006;
  box-shadow: 0 0 20px rgba(245, 197, 66, 0.45);
  animation: pulse-ring 2s infinite;
}

.step.done .step-dot {
  background: var(--cabbage-dim);
  border-color: rgba(74, 222, 128, 0.45);
  color: var(--cabbage);
}

.check {
  font-size: 0.75rem;
}

.step-label {
  font-size: 0.68rem;
  color: var(--text-muted);
  text-align: center;
  max-width: 80px;
  line-height: 1.3;
  font-weight: 500;
}

.step.active .step-label {
  color: var(--gold);
  font-weight: 700;
}
</style>
