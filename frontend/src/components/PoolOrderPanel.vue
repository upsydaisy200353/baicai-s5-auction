<script setup lang="ts">
import { ref } from 'vue'
import { POSITION_NAMES, POSITION_TO_LETTER, POSITIONS } from '../constants'
import type { Position } from '../types'

const emit = defineEmits<{
  confirm: [order: Position[]]
}>()

const order = ref<Position[]>([...POSITIONS])

function moveUp(index: number) {
  if (index <= 0) return
  const next = [...order.value]
  ;[next[index - 1], next[index]] = [next[index], next[index - 1]!]
  order.value = next
}

function moveDown(index: number) {
  if (index >= order.value.length - 1) return
  const next = [...order.value]
  ;[next[index], next[index + 1]] = [next[index + 1]!, next[index]]
  order.value = next
}

function shuffle() {
  const next = [...POSITIONS]
  for (let i = next.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[next[i], next[j]] = [next[j]!, next[i]!]
  }
  order.value = next
}

function onConfirm() {
  emit('confirm', [...order.value])
}
</script>

<template>
  <div class="pool-order-panel card">
    <h3 class="panel-title">确定位置池拍卖顺序</h3>
    <p class="panel-desc">共 5 个位置池，由管理员设定先后拍卖顺序（8 位队长无需选池）</p>

    <ol class="order-list">
      <li v-for="(pos, i) in order" :key="pos" class="order-item">
        <span class="order-num">{{ i + 1 }}</span>
        <span class="order-label">
          {{ POSITION_TO_LETTER[pos] }}. {{ POSITION_NAMES[pos] }}
        </span>
        <span class="order-actions">
          <button type="button" class="btn-ghost btn-xs" :disabled="i === 0" @click="moveUp(i)">
            ↑
          </button>
          <button
            type="button"
            class="btn-ghost btn-xs"
            :disabled="i === order.length - 1"
            @click="moveDown(i)"
          >
            ↓
          </button>
        </span>
      </li>
    </ol>

    <div class="panel-actions">
      <button type="button" class="btn-ghost" @click="shuffle">随机打乱</button>
      <button type="button" class="btn-primary" @click="onConfirm">确认位置池顺序</button>
    </div>
  </div>
</template>

<style scoped>
.pool-order-panel {
  margin-bottom: 1rem;
  padding: 1rem 1.25rem;
}

.panel-title {
  font-size: 0.9375rem;
  font-weight: 700;
  margin-bottom: 0.35rem;
}

.panel-desc {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.order-list {
  list-style: none;
  margin: 0 0 1rem;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.order-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--bg-hover);
  border-radius: 8px;
}

.order-num {
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  background: var(--accent-glow);
  color: var(--accent);
  font-size: 0.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.order-label {
  flex: 1;
  font-size: 0.875rem;
  font-weight: 600;
}

.order-actions {
  display: flex;
  gap: 0.25rem;
}

.btn-xs {
  padding: 0.2rem 0.45rem;
  font-size: 0.75rem;
  min-width: 2rem;
}

.panel-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
</style>
