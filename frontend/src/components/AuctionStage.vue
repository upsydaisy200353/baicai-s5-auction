<script setup lang="ts">
import { POSITION_NAMES, POSITION_TO_LETTER } from '../constants'
import type { AuctionPhase, Player, Position } from '../types'

defineProps<{
  phase: AuctionPhase
  currentPlayer: Player | null
  currentPool: Position | null
  poolOrder: Position[]
}>()

const phaseLabel: Record<AuctionPhase, string> = {
  idle: '待开始',
  intro: '开场介绍',
  pool_select: '设定池顺序',
  pool_announce: '进入位置池',
  pool_draw: '随机抽取',
  bidding: '竞拍中',
  winner_reveal: '成交公布',
  player_done: '过渡',
  finished: '仪式结束',
}

function poolChipLabel(pos: Position) {
  return `${POSITION_TO_LETTER[pos]}. ${POSITION_NAMES[pos]}`
}
</script>

<template>
  <div class="stage card">
    <div class="stage-header">
      <span class="badge badge-blue">{{ phaseLabel[phase] }}</span>
      <span v-if="currentPool" class="pool-tag">
        {{ POSITION_NAMES[currentPool] }}
      </span>
    </div>

    <div v-if="poolOrder.length" class="pool-order">
      <span class="order-label">拍卖顺序</span>
      <div class="order-chips">
        <span
          v-for="(pos, i) in poolOrder"
          :key="pos + i"
          class="chip"
          :class="{ active: pos === currentPool }"
        >
          {{ poolChipLabel(pos) }}
        </span>
      </div>
    </div>

    <div v-if="phase === 'pool_select'" class="pool-select-hint">
      <span class="hint-label">等待管理员</span>
      <span>确定五个位置池的拍卖顺序</span>
    </div>

    <div v-if="currentPlayer && phase === 'bidding'" class="current-player">
      <div class="player-avatar">{{ currentPlayer.serial }}</div>
      <div class="player-detail">
        <h2 class="player-name">{{ currentPlayer.name }}</h2>
        <div class="price-row">
          <span>起拍 <strong>{{ currentPlayer.startPrice }}w</strong></span>
          <span>一口价 <strong class="gold">{{ currentPlayer.buyoutPrice }}w</strong></span>
        </div>
      </div>
    </div>

    <div v-else-if="phase === 'idle'" class="stage-empty">
      <div class="empty-icon">🏆</div>
      <p>点击「开始仪式」</p>
      <p class="hint">流程参考白菜杯 S4 选人仪式录像</p>
    </div>
  </div>
</template>

<style scoped>
.stage {
  min-height: 160px;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.stage-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.pool-tag {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.pool-order .order-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  display: block;
  margin-bottom: 0.35rem;
}

.order-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.chip {
  font-size: 0.75rem;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  background: var(--bg-hover);
  color: var(--text-muted);
}

.chip.active {
  background: var(--accent-glow);
  color: var(--accent);
  border: 1px solid var(--accent);
}

.pool-select-hint {
  padding: 0.75rem 1rem;
  background: var(--gold-dim);
  border-radius: 8px;
  border: 1px solid rgba(245, 158, 11, 0.3);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.hint-label {
  color: var(--text-muted);
}

.hint-rating {
  font-size: 0.75rem;
  color: var(--gold);
}

.current-player {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding: 1rem;
  background: var(--bg-hover);
  border-radius: var(--radius);
  border: 1px solid var(--border);
}

.player-avatar {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1.1rem;
  flex-shrink: 0;
}

.player-name {
  font-size: 1.5rem;
  margin-bottom: 0.35rem;
}

.price-row {
  display: flex;
  gap: 1.5rem;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.price-row strong { color: var(--text); }
.price-row .gold { color: var(--gold); }

.stage-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: var(--text-muted);
  padding: 1.5rem;
}

.empty-icon { font-size: 2rem; }
.hint { font-size: 0.8125rem; opacity: 0.7; }
</style>
