<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Captain } from '../types'

const props = defineProps<{
  captains: Captain[]
  savedOrder: string[]
  poolLabel?: string
  confirmLabel?: string
}>()

const emit = defineEmits<{
  confirm: [names: string[]]
}>()

function defaultOrder(caps: Captain[]) {
  return [...caps].sort((a, b) => b.rating - a.rating).map((c) => c.name)
}

const order = ref<string[]>([])
const dragIndex = ref<number | null>(null)
const overIndex = ref<number | null>(null)

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

function reorder(from: number, to: number) {
  if (from === to || from < 0 || to < 0 || from >= order.value.length || to >= order.value.length) {
    return
  }
  const next = [...order.value]
  const [item] = next.splice(from, 1)
  next.splice(to, 0, item!)
  order.value = next
}

function moveUp(index: number) {
  if (index <= 0) return
  reorder(index, index - 1)
}

function moveDown(index: number) {
  if (index >= order.value.length - 1) return
  reorder(index, index + 1)
}

function onDragStart(index: number, e: DragEvent) {
  dragIndex.value = index
  overIndex.value = index
  e.dataTransfer?.setData('text/plain', String(index))
  if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
}

function onDragOver(index: number, e: DragEvent) {
  e.preventDefault()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
  overIndex.value = index
}

function onDrop(index: number, e: DragEvent) {
  e.preventDefault()
  const from = dragIndex.value
  if (from != null) reorder(from, index)
  dragIndex.value = null
  overIndex.value = null
}

function onDragEnd() {
  dragIndex.value = null
  overIndex.value = null
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
    <h3 class="panel-title">
      队长出价顺序
      <span v-if="poolLabel" class="pool-tag">{{ poolLabel }}</span>
    </h3>
    <p class="panel-desc">
      拖拽调整先后，或使用 ↑↓ 微调。
      <template v-if="confirmLabel?.includes('抽签')">
        确认后将开始<strong>随机抽签</strong>并进入拍卖。
      </template>
      <template v-else>
        可先设定顺序；确认位置池后将进入各池出价顺序确认。
      </template>
    </p>

    <ol class="order-list">
      <li
        v-for="(name, i) in order"
        :key="name"
        class="order-item"
        :class="{
          dragging: dragIndex === i,
          'drop-over': overIndex === i && dragIndex !== null && dragIndex !== i,
        }"
        draggable="true"
        @dragstart="onDragStart(i, $event)"
        @dragover="onDragOver(i, $event)"
        @drop="onDrop(i, $event)"
        @dragend="onDragEnd"
      >
        <span class="drag-handle" title="拖拽排序" aria-hidden="true">⋮⋮</span>
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
      <button type="button" class="btn-primary" @click="onConfirm">
        {{ confirmLabel || '保存出价顺序' }}
      </button>
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
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.pool-tag {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--gold);
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  background: var(--gold-dim);
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
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: var(--bg-hover);
  border-radius: 8px;
  border: 1px solid transparent;
  cursor: grab;
  user-select: none;
  transition: border-color 0.15s, box-shadow 0.15s, opacity 0.15s;
}

.order-item:active {
  cursor: grabbing;
}

.order-item.dragging {
  opacity: 0.45;
  border-color: var(--accent);
}

.order-item.drop-over {
  border-color: var(--gold);
  box-shadow: 0 0 0 1px var(--gold-dim);
}

.drag-handle {
  color: var(--text-muted);
  font-size: 0.75rem;
  letter-spacing: -0.15em;
  line-height: 1;
  padding: 0.15rem 0.1rem;
  flex-shrink: 0;
  opacity: 0.7;
}

.order-item:hover .drag-handle {
  opacity: 1;
  color: var(--accent);
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
