<script setup lang="ts">
import { computed } from 'vue'
import { POSITION_COLORS, POSITION_NAMES, POSITION_TO_LETTER } from '../constants'
import { playSound, unlockAudio } from '../lib/soundEngine'
import type { Position } from '../types'

const props = defineProps<{
  availablePools: Position[]
  poolOrder: Position[]
}>()

const emit = defineEmits<{
  select: [pool: Position]
}>()

const completedCount = computed(() => props.poolOrder.length)
const isFirstPick = computed(() => props.poolOrder.length === 0)

function poolLabel(pos: Position) {
  return `${POSITION_TO_LETTER[pos]}. ${POSITION_NAMES[pos]}`
}

function onSelect(pool: Position) {
  void unlockAudio()
  playSound('poolSelect')
  emit('select', pool)
}
</script>

<template>
  <div class="pool-pick-panel card">
    <h3 class="panel-title">
      {{ isFirstPick ? '选择首个位置池' : '选择下一个位置池' }}
    </h3>
    <p class="panel-desc">
      已拍卖 <strong>{{ completedCount }}</strong> / 5 个位置池
      <span v-if="availablePools.length">· 剩余 {{ availablePools.length }} 个可选</span>
    </p>

    <div v-if="poolOrder.length" class="done-section">
      <span class="done-label">已拍卖顺序</span>
      <div class="done-chips">
        <span
          v-for="(pos, i) in poolOrder"
          :key="pos + String(i)"
          class="done-chip"
          :style="{ '--chip-color': POSITION_COLORS[pos] }"
        >
          <span class="done-num">{{ i + 1 }}</span>
          {{ poolLabel(pos) }}
        </span>
      </div>
    </div>

    <div v-if="availablePools.length" class="pool-grid">
      <button
        v-for="pos in availablePools"
        :key="pos"
        type="button"
        class="pool-btn"
        :style="{ '--pool-color': POSITION_COLORS[pos] }"
        @click="onSelect(pos)"
      >
        <span class="pool-letter">{{ POSITION_TO_LETTER[pos] }}</span>
        <span class="pool-name">{{ POSITION_NAMES[pos] }}</span>
        <span class="pool-action">开始拍卖 →</span>
      </button>
    </div>
    <p v-else class="empty-hint">所有位置池已拍卖完毕</p>
  </div>
</template>

<style scoped>
.pool-pick-panel {
  margin-bottom: 1rem;
  padding: 1.1rem 1.25rem;
}

.panel-title {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 0.35rem;
}

.panel-desc {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.panel-desc strong {
  color: var(--gold);
}

.done-section {
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.18);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}

.done-label {
  display: block;
  font-size: 0.68rem;
  color: var(--text-muted);
  letter-spacing: 0.06em;
  margin-bottom: 0.45rem;
}

.done-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.done-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--chip-color) 12%, transparent);
  color: var(--chip-color);
  border: 1px solid color-mix(in srgb, var(--chip-color) 28%, transparent);
}

.done-num {
  font-size: 0.62rem;
  opacity: 0.75;
}

.pool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.65rem;
}

.pool-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.2rem;
  padding: 0.85rem 1rem;
  text-align: left;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background 0.18s ease;
}

.pool-btn:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--pool-color) 45%, transparent);
  background: color-mix(in srgb, var(--pool-color) 10%, transparent);
  box-shadow: 0 8px 24px color-mix(in srgb, var(--pool-color) 18%, transparent);
}

.pool-letter {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--pool-color);
}

.pool-name {
  font-size: 0.9rem;
  font-weight: 700;
}

.pool-action {
  font-size: 0.68rem;
  color: var(--text-muted);
  margin-top: 0.15rem;
}

.empty-hint {
  font-size: 0.8125rem;
  color: var(--text-muted);
  text-align: center;
  padding: 1rem;
}
</style>
