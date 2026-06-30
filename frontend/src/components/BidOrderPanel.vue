<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Captain } from '../types'

const props = defineProps<{
  captains: Captain[]
  savedOrder: string[]
}>()

const emit = defineEmits<{
  confirm: [names: string[]]
}>()

function defaultOrder(caps: Captain[]) {
  return [...caps].sort((a, b) => b.rating - a.rating).map((c) => c.name)
}

const order = ref<string[]>([])

watch(
  () => [props.captains, props.savedOrder] as const,
  () => {
    if (props.savedOrder.length === props.captains.length) {
      order.value = [...props.savedOrder]
    } else {
      order.value = defaultOrder(props.captains)
    }
  },
  { immediate: true },
)

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

function resetDefault() {
  order.value = defaultOrder(props.captains)
}

function onConfirm() {
  emit('confirm', [...order.value])
}
</script>

<template>
  <div class="bid-order-panel card">
    <h3 class="panel-title">队长出价顺序</h3>
    <p class="panel-desc">
      管理员设定各队长竞价先后；保存后从<strong>下一轮</strong>起生效。未设定时首轮按实力、后续按资金。
    </p>

    <ol class="order-list">
      <li v-for="(name, i) in order" :key="name" class="order-item">
        <span class="order-num">{{ i + 1 }}</span>
        <span class="order-label">{{ name }}</span>
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
      <button type="button" class="btn-ghost" @click="resetDefault">恢复默认（实力排序）</button>
      <button type="button" class="btn-primary" @click="onConfirm">保存出价顺序</button>
    </div>
  </div>
</template>

<style scoped>
.bid-order-panel {
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
