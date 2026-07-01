<script setup lang="ts">
import { computed } from 'vue'
import { POSITION_COLORS, POSITION_NAMES, POSITION_TO_LETTER } from '../constants'
import PlayerAvatar from './PlayerAvatar.vue'
import type { AuctionPhase, Player, Position } from '../types'

const props = defineProps<{
  phase: AuctionPhase
  currentPlayer: Player | null
  currentPool: Position | null
  poolOrder: Position[]
}>()

const phaseLabel: Record<AuctionPhase, string> = {
  idle: '待开始',
  intro: '开场介绍',
  pool_select: '选择位置池',
  bid_order_select: '设定出价顺序',
  pool_announce: '进入位置池',
  pool_draw: '随机抽取',
  bidding: '竞拍中',
  winner_reveal: '成交公布',
  player_done: '过渡',
  finished: '仪式结束',
}

const poolColor = computed(() =>
  props.currentPool ? POSITION_COLORS[props.currentPool] : 'var(--accent)',
)

function poolChipLabel(pos: Position) {
  return `${POSITION_TO_LETTER[pos]}. ${POSITION_NAMES[pos]}`
}
</script>

<template>
  <div class="stage card fade-in" :class="{ live: phase === 'bidding' }">
    <img
      v-if="phase === 'idle'"
      src="/images/auction-accent.png"
      alt=""
      class="stage-accent"
      aria-hidden="true"
    />
    <div class="stage-glow" :style="{ '--pool-color': poolColor }" />

    <div class="stage-header">
      <span class="phase-badge">{{ phaseLabel[phase] }}</span>
      <span v-if="currentPool" class="pool-tag" :style="{ '--pool-color': poolColor }">
        {{ POSITION_NAMES[currentPool] }}
      </span>
      <span v-if="phase === 'bidding'" class="live-dot">LIVE</span>
    </div>

    <div v-if="poolOrder.length" class="pool-order">
      <span class="order-label">
        拍卖进度
        <span v-if="currentPool" class="order-sub">· 当前 {{ poolChipLabel(currentPool) }}</span>
      </span>
      <div class="order-chips">
        <span
          v-for="(pos, i) in poolOrder"
          :key="pos + i"
          class="chip"
          :class="{ active: pos === currentPool, done: pos !== currentPool && phase !== 'pool_select' }"
          :style="{ '--chip-color': POSITION_COLORS[pos] }"
        >
          <span class="chip-num">{{ i + 1 }}</span>
          {{ poolChipLabel(pos) }}
        </span>
      </div>
    </div>

    <div v-if="phase === 'pool_select'" class="pool-select-hint">
      <span class="hint-icon">🎯</span>
      <div>
        <span class="hint-label">管理员选池中</span>
        <span>从剩余位置池中选择下一个要拍卖的池子</span>
      </div>
    </div>

    <div v-else-if="phase === 'bid_order_select'" class="pool-select-hint">
      <span class="hint-icon">⚙</span>
      <div>
        <span class="hint-label">管理员配置中</span>
        <span>设定本池队长出价顺序后开始抽签</span>
      </div>
    </div>

    <div
      v-if="currentPlayer && phase === 'bidding'"
      class="current-player"
      :style="{ '--pool-color': POSITION_COLORS[currentPlayer.position] }"
    >
      <div class="player-detail">
        <p class="player-eyebrow">当前拍卖选手</p>
        <p class="player-serial">{{ currentPlayer.serial }}</p>
        <h2 class="player-name">{{ currentPlayer.name }}</h2>
        <div class="price-row">
          <div class="price-block">
            <span class="price-label">起拍</span>
            <strong>{{ currentPlayer.startPrice }}<small>w</small></strong>
          </div>
          <div class="price-divider" />
          <div class="price-block gold">
            <span class="price-label">一口价</span>
            <strong>{{ currentPlayer.buyoutPrice }}<small>w</small></strong>
          </div>
        </div>
      </div>
      <div class="player-splash">
        <img
          v-if="currentPlayer.avatar"
          :src="currentPlayer.avatar"
          :alt="currentPlayer.name"
          class="splash-img"
        />
        <PlayerAvatar
          v-else
          :name="currentPlayer.name"
          :serial="currentPlayer.serial"
          :position="currentPlayer.position"
          size="xl"
        />
      </div>
    </div>

    <div v-else-if="phase === 'idle'" class="stage-empty">
      <img src="/logo.svg" alt="" class="empty-logo" />
      <p class="empty-title">仪式尚未开始</p>
      <p class="hint">点击「开始仪式」进入白菜杯 S5 选人现场</p>
    </div>
  </div>
</template>

<style scoped>
.stage {
  min-height: 180px;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  overflow: hidden;
}

.stage-accent {
  position: absolute;
  right: -8%;
  bottom: -18%;
  width: min(280px, 55%);
  opacity: 0.14;
  pointer-events: none;
  filter: saturate(1.1);
  animation: accentFloat 8s ease-in-out infinite alternate;
}

@keyframes accentFloat {
  from { transform: translateY(0) rotate(-2deg); }
  to { transform: translateY(-8px) rotate(2deg); }
}

.stage.live {
  border-color: rgba(245, 197, 66, 0.35);
  box-shadow: var(--shadow-card), 0 0 48px rgba(245, 197, 66, 0.08);
}

.stage-glow {
  position: absolute;
  top: -40%;
  right: -10%;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--pool-color) 25%, transparent), transparent 70%);
  pointer-events: none;
}

.stage-header {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
  position: relative;
  z-index: 1;
}

.phase-badge {
  font-family: var(--font-display);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  background: var(--accent-glow);
  color: var(--accent);
}

.pool-tag {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--pool-color);
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--pool-color) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--pool-color) 30%, transparent);
}

.live-dot {
  font-family: var(--font-display);
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  color: #ef4444;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.live-dot::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ef4444;
  animation: pulse-ring 1.5s infinite;
}

.pool-order .order-label {
  font-size: 0.72rem;
  color: var(--text-muted);
  display: block;
  margin-bottom: 0.45rem;
  letter-spacing: 0.04em;
}

.order-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.chip {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.25rem 0.7rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-muted);
  border: 1px solid var(--border);
  transition: all 0.2s ease;
}

.chip.active {
  background: color-mix(in srgb, var(--chip-color) 15%, transparent);
  color: var(--chip-color);
  border-color: color-mix(in srgb, var(--chip-color) 40%, transparent);
  box-shadow: 0 0 16px color-mix(in srgb, var(--chip-color) 20%, transparent);
}

.chip.done {
  opacity: 0.55;
}

.chip-num {
  font-size: 0.62rem;
  opacity: 0.7;
  margin-right: 0.15rem;
}

.order-sub {
  color: var(--gold);
  font-weight: 600;
}

.pool-select-hint {
  padding: 0.85rem 1rem;
  background: var(--gold-dim);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(245, 197, 66, 0.22);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.875rem;
}

.hint-icon {
  font-size: 1.25rem;
  opacity: 0.8;
}

.hint-label {
  display: block;
  font-size: 0.72rem;
  color: var(--gold);
  font-weight: 700;
  letter-spacing: 0.04em;
  margin-bottom: 0.1rem;
}

.current-player {
  display: flex;
  align-items: stretch;
  gap: 1rem;
  padding: 1rem 1rem 1rem 1.15rem;
  background: rgba(0, 0, 0, 0.22);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  animation: fadeUp 0.4s ease;
  position: relative;
  z-index: 1;
  min-height: 200px;
}

.player-detail {
  flex: 0 0 38%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0.25rem 0;
}

.player-serial {
  font-family: var(--font-display);
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--pool-color, var(--accent));
  margin-bottom: 0.25rem;
  letter-spacing: 0.06em;
}

.player-splash {
  flex: 1;
  min-width: 0;
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.35rem 0.5rem;
  border-radius: var(--radius-sm);
  background:
    radial-gradient(
      ellipse 80% 70% at 50% 50%,
      color-mix(in srgb, var(--pool-color) 12%, transparent),
      transparent 70%
    ),
    rgba(0, 0, 0, 0.15);
  border: 1px solid color-mix(in srgb, var(--pool-color) 18%, transparent);
}

.splash-img {
  display: block;
  max-width: 100%;
  max-height: min(240px, 42vw);
  width: auto;
  height: auto;
  object-fit: contain;
  object-position: center center;
  border-radius: 10px;
  filter: drop-shadow(0 8px 24px rgba(0, 0, 0, 0.45));
  animation: splashIn 0.45s ease;
}

@keyframes splashIn {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@media (max-width: 640px) {
  .current-player {
    flex-direction: column;
    min-height: auto;
  }

  .player-detail {
    flex: none;
  }

  .player-splash {
    min-height: 160px;
  }

  .splash-img {
    max-height: 200px;
  }
}

.player-eyebrow {
  font-size: 0.68rem;
  color: var(--text-muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 0.2rem;
}

.player-name {
  font-family: var(--font-display);
  font-size: 1.6rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
  background: linear-gradient(90deg, #fff, var(--gold-bright));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.price-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.price-block {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.price-label {
  font-size: 0.68rem;
  color: var(--text-muted);
}

.price-block strong {
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 800;
}

.price-block strong small {
  font-size: 0.7rem;
  opacity: 0.75;
}

.price-block.gold strong {
  color: var(--gold);
}

.price-divider {
  width: 1px;
  height: 28px;
  background: var(--border);
}

.stage-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: var(--text-muted);
  padding: 1.5rem;
  position: relative;
  z-index: 1;
}

.empty-logo {
  width: 56px;
  height: 56px;
  opacity: 0.7;
  margin-bottom: 0.25rem;
}

.empty-title {
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text);
}

.hint {
  font-size: 0.8125rem;
  opacity: 0.75;
}
</style>
