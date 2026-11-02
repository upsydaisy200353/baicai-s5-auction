<script setup lang="ts">
import { computed } from 'vue'
import { POSITION_NAMES } from '../constants'
import type { Player, Position } from '../types'

const props = defineProps<{
  players: Player[]
  currentPlayerSerial?: string | null
}>()

const POSITIONS: Position[] = ['Top', 'Jungle', 'Mid', 'Bot', 'Support']

interface PositionGroup {
  key: Position
  label: string
  sold: Player[]
  remaining: Player[]
  unsold: Player[]
  total: number
}

function unsoldStartPrice(player: Player): number {
  const original = Number(player.originalStartPrice ?? player.startPrice) || 0
  const scaled = Math.max(10, original) * 1.2
  const floor = Math.floor(scaled)
  const fraction = scaled - floor
  const rounded = Math.abs(fraction - 0.5) < 1e-9
    ? (floor % 2 === 0 ? floor : floor + 1)
    : Math.round(scaled)
  return Math.max(10, rounded)
}

const groups = computed<PositionGroup[]>(() =>
  POSITIONS.map((key) => {
    const list = props.players.filter((p) => p.position === key)
    return {
      key,
      label: POSITION_NAMES[key] ?? key,
      sold: list.filter((p) => p.sold),
      unsold: list.filter((p) => !p.sold && (p.inUnsoldPool || p.excluded)),
      remaining: list.filter((p) => !p.sold && !p.inUnsoldPool && !p.excluded),
      total: list.length,
    }
  }),
)

const totals = computed(() => {
  const sold = props.players.filter((p) => p.sold).length
  const unsold = props.players.filter((p) => !p.sold && (p.inUnsoldPool || p.excluded)).length
  return {
    sold,
    unsold,
    remaining: props.players.length - sold - unsold,
    all: props.players.length,
  }
})
</script>

<template>
  <section class="player-status card" aria-label="选手状态看板">
    <header class="ps-head">
      <div class="ps-heading">
        <h3 class="ps-title">选手状态</h3>
        <p class="ps-sub">按位置分类 · 实时同步</p>
      </div>
      <div class="ps-totals">
        <span class="ps-chip sold">已成交 {{ totals.sold }}</span>
        <span class="ps-chip left">剩余 {{ totals.remaining }}</span>
        <span class="ps-chip unsold">流拍 {{ totals.unsold }}</span>
        <span class="ps-chip all">共 {{ totals.all }}</span>
      </div>
    </header>

    <div class="ps-grid">
      <article v-for="g in groups" :key="g.key" class="ps-col">
        <header class="ps-col-head">
          <span class="ps-pos">{{ g.label }}</span>
          <span class="ps-count">{{ g.sold.length }}/{{ g.total }}</span>
        </header>

        <div v-if="g.remaining.length" class="ps-block">
          <p class="ps-block-title left">剩余 {{ g.remaining.length }}</p>
          <ul class="ps-list">
            <li
              v-for="p in g.remaining"
              :key="p.serial"
              :class="['ps-item', { current: p.serial === props.currentPlayerSerial }]"
            >
              <span class="ps-name">{{ p.name }}</span>
              <span class="ps-meta">{{ p.startPrice }}w 起</span>
            </li>
          </ul>
        </div>

        <div v-if="g.sold.length" class="ps-block">
          <p class="ps-block-title sold">已成交 {{ g.sold.length }}</p>
          <ul class="ps-list">
            <li v-for="p in g.sold" :key="p.serial" class="ps-item sold">
              <span class="ps-name">{{ p.name }}</span>
              <span class="ps-meta">
                <template v-if="p.finalPrice">{{ p.finalPrice }}w</template>
                <template v-else>已拍出</template>
              </span>
            </li>
          </ul>
        </div>

        <div v-if="g.unsold.length" class="ps-block">
          <p class="ps-block-title unsold">流拍池 {{ g.unsold.length }}</p>
          <ul class="ps-list">
            <li v-for="p in g.unsold" :key="p.serial" class="ps-item unsold">
              <span class="ps-name">{{ p.name }}</span>
              <span class="ps-meta">{{ p.excluded ? '不再重拍' : '重拍 ' + unsoldStartPrice(p) + 'w 起' }}</span>
            </li>
          </ul>
        </div>

        <p v-if="!g.total" class="ps-empty">该位置暂无选手</p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.player-status {
  padding: 1rem 1.15rem;
  margin-top: 1rem;
  border-color: rgba(245, 197, 66, 0.18);
}

.ps-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.85rem;
}

.ps-title {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--gold);
}

.ps-sub {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-top: 0.15rem;
}

.ps-totals {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.ps-chip {
  font-size: 0.72rem;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  color: var(--text-muted);
  white-space: nowrap;
}

.ps-chip.sold {
  color: #34d399;
  border-color: rgba(52, 211, 153, 0.35);
  background: rgba(52, 211, 153, 0.08);
}

.ps-chip.left {
  color: #7dd3fc;
  border-color: rgba(125, 211, 252, 0.3);
  background: rgba(125, 211, 252, 0.07);
}

.ps-chip.unsold {
  color: #f87171;
  border-color: rgba(248, 113, 113, 0.3);
  background: rgba(248, 113, 113, 0.07);
}

.ps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.65rem;
}

.ps-col {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.6rem 0.65rem;
  background: rgba(255, 255, 255, 0.015);
  min-height: 80px;
}

.ps-col-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 0.4rem;
  margin-bottom: 0.4rem;
  border-bottom: 1px dashed var(--border);
}

.ps-pos {
  font-family: var(--font-display);
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text);
}

.ps-count {
  font-size: 0.72rem;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.ps-block + .ps-block {
  margin-top: 0.45rem;
}

.ps-block-title {
  font-size: 0.68rem;
  letter-spacing: 0.06em;
  margin-bottom: 0.2rem;
  color: var(--text-muted);
}

.ps-block-title.sold {
  color: #34d399;
}

.ps-block-title.left {
  color: #7dd3fc;
}

.ps-block-title.unsold {
  color: #f87171;
}

.ps-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.ps-item {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.4rem;
  font-size: 0.78rem;
  padding: 0.12rem 0.3rem;
  border-radius: 4px;
  color: var(--text);
}

.ps-item.current {
  background: rgba(245, 197, 66, 0.14);
  box-shadow: inset 0 0 0 1px rgba(245, 197, 66, 0.35);
}

.ps-item.sold .ps-name {
  color: var(--text-muted);
  text-decoration: line-through;
  text-decoration-color: rgba(52, 211, 153, 0.6);
}

.ps-item.unsold .ps-name {
  color: var(--text-muted);
}

.ps-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ps-meta {
  flex-shrink: 0;
  font-size: 0.7rem;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.ps-empty {
  font-size: 0.72rem;
  color: var(--text-muted);
  text-align: center;
  padding: 0.6rem 0;
}
</style>
