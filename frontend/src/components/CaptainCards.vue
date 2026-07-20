<script setup lang="ts">
import { computed } from 'vue'
import { POOL_LETTERS, POSITION_COLORS, POSITION_NAMES } from '../constants'
import { captainOccupiedPositions } from '../rosterUtils'
import PlayerAvatar from './PlayerAvatar.vue'
import type { Captain, Player, Position } from '../types'

const props = defineProps<{
  captains: Captain[]
  activeName?: string | null
  currentPosition?: Position | null
  players?: Player[]
  ineligibleNames?: string[]
  ineligibleReasons?: Record<string, string>
}>()

const sorted = computed(() =>
  [...props.captains].sort((a, b) => b.rating - a.rating),
)

function isIneligible(cap: Captain) {
  return props.ineligibleNames?.includes(cap.name) ?? false
}

function skipReason(cap: Captain) {
  return props.ineligibleReasons?.[cap.name]
}

function ownPosition(cap: Captain): Position {
  return POOL_LETTERS[cap.poolLetter]
}
</script>

<template>
  <div class="captain-grid">
    <div
      v-for="(cap, i) in sorted"
      :key="cap.name"
      class="captain-card card"
      :class="{
        active: cap.name === activeName,
        broke: cap.funds <= 0,
        ineligible: isIneligible(cap),
      }"
      :style="{ '--delay': `${i * 0.04}s` }"
    >
      <div class="card-shine" />
      <div class="cap-top">
        <PlayerAvatar
          :name="cap.name"
          :avatar="cap.avatar"
          :position="ownPosition(cap)"
          size="md"
        />
        <div class="cap-meta">
          <span class="cap-name">{{ cap.name }}</span>
          <span class="badge badge-blue">实力 {{ cap.rating }}</span>
          <span v-if="cap.tier" class="badge badge-gold">{{ cap.tier }}</span>
        </div>
      </div>
      <p class="own-pos" :style="{ color: POSITION_COLORS[ownPosition(cap)] }">
        {{ POSITION_NAMES[ownPosition(cap)] }}
      </p>
      <div class="cap-funds">
        <span class="label">剩余资金</span>
        <span class="amount">{{ cap.funds }}<small>w</small></span>
      </div>
      <div class="funds-bar">
        <div class="funds-fill" :style="{ width: `${Math.min(100, cap.funds / 10)}%` }" />
      </div>
      <p v-if="isIneligible(cap) && currentPosition" class="skip-hint">
        {{ skipReason(cap) || '本场不参与' }}
      </p>
      <div v-if="cap.team.length" class="cap-team">
        <span class="label">队员</span>
        <div class="team-tags">
          <span v-for="name in cap.team" :key="name" class="team-tag">
            {{ name }}
            <small v-if="players?.find((p) => p.name === name)">
              {{ POSITION_NAMES[players!.find((p) => p.name === name)!.position] }}
            </small>
          </span>
        </div>
      </div>
      <div
        v-else-if="players?.length && captainOccupiedPositions(cap, players).length === 1"
        class="cap-team"
      >
        <span class="label muted-only">暂无竞拍队员</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.captain-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 0.75rem;
}

.captain-card {
  transition:
    transform 0.22s ease,
    border-color 0.22s ease,
    box-shadow 0.22s ease;
  animation: fadeUp 0.45s ease both;
  animation-delay: var(--delay);
  overflow: hidden;
}

.captain-card:hover:not(.ineligible) {
  transform: translateY(-3px);
}

.captain-card.active {
  border-color: rgba(245, 197, 66, 0.5);
  box-shadow: 0 0 28px rgba(245, 197, 66, 0.18);
}

.captain-card.active .card-shine {
  opacity: 1;
}

.card-shine {
  position: absolute;
  top: 0;
  left: -100%;
  width: 60%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.06), transparent);
  opacity: 0;
  animation: shine 3s ease-in-out infinite;
  pointer-events: none;
}

@keyframes shine {
  0% { left: -100%; opacity: 0; }
  50% { opacity: 1; }
  100% { left: 200%; opacity: 0; }
}

.captain-card.broke {
  opacity: 0.48;
  filter: grayscale(0.4);
}

.captain-card.ineligible {
  opacity: 0.58;
}

.cap-top {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 0.5rem;
}

.cap-meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}

.cap-name {
  font-weight: 700;
  font-size: 0.95rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.own-pos {
  font-size: 0.72rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.cap-funds {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.35rem;
}

.funds-bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 0.55rem;
}

.funds-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--gold), var(--cabbage));
  border-radius: 2px;
  transition: width 0.5s ease;
}

.skip-hint {
  font-size: 0.68rem;
  color: var(--text-muted);
  margin-bottom: 0.45rem;
  padding: 0.25rem 0.45rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
}

.label {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.muted-only {
  opacity: 0.7;
}

.amount {
  font-family: var(--font-display);
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--gold);
}

.amount small {
  font-size: 0.72rem;
  opacity: 0.75;
}

.cap-team .team-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-top: 0.3rem;
}

.team-tag {
  font-size: 0.68rem;
  background: rgba(255, 255, 255, 0.04);
  padding: 0.15rem 0.45rem;
  border-radius: 6px;
  color: var(--text-muted);
  border: 1px solid var(--border);
}

.team-tag small {
  opacity: 0.8;
  margin-left: 0.15rem;
}
</style>
