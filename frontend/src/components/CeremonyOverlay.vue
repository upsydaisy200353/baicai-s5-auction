<script setup lang="ts">
import { ref, watch, onUnmounted, computed } from 'vue'
import { POSITION_NAMES } from '../constants'
import PlayerAvatar from './PlayerAvatar.vue'
import type { Captain, LastResult, Player, Position } from '../types'

const props = defineProps<{
  phase: string
  captains: Captain[]
  currentPool: Position | null
  poolOrder: Position[]
  drawCandidates: Player[]
  lastResult: LastResult | null
  isAdmin?: boolean
}>()

const emit = defineEmits<{
  begin: []
  confirmPool: []
  revealDraw: []
  confirmWinner: []
}>()

// 抽签轮播动画
const spinName = ref('???')
const spinning = ref(false)
let spinTimer: ReturnType<typeof setInterval> | null = null

function startSpin() {
  if (!props.drawCandidates.length) return
  spinning.value = true
  let tick = 0
  const names = props.drawCandidates.map((p) => p.name)
  spinTimer = setInterval(() => {
    spinName.value = names[tick % names.length]!
    tick++
    if (tick > 28) {
      stopSpin()
      if (props.isAdmin) {
        emit('revealDraw')
      }
    }
  }, 80)
}

function stopSpin() {
  if (spinTimer) clearInterval(spinTimer)
  spinTimer = null
  spinning.value = false
}

function maybeStartSpin() {
  if (props.phase !== 'pool_draw' || !props.drawCandidates.length) return
  if (spinning.value || spinTimer) return
  spinName.value = '???'
  setTimeout(startSpin, 400)
}

watch(
  () => [props.phase, props.drawCandidates.length] as const,
  ([phase]) => {
    if (phase === 'pool_draw') {
      maybeStartSpin()
    } else {
      stopSpin()
      spinName.value = '???'
    }
  },
  { immediate: true },
)

onUnmounted(stopSpin)

const revealedDrawPlayer = computed(() => {
  if (props.phase !== 'pool_draw' || spinning.value || spinName.value === '???') {
    return null
  }
  return props.drawCandidates.find((p) => p.name === spinName.value) ?? null
})
</script>

<template>
  <!-- 开场 -->
  <div v-if="phase === 'intro'" class="overlay intro">
    <div class="overlay-bg" aria-hidden="true" />
    <div class="overlay-card card-pop">
      <img src="/logo.svg" alt="" class="intro-logo" />
      <p class="eyebrow">BAICAI CUP · S5</p>
      <h2 class="overlay-title">选人仪式</h2>
      <p class="overlay-desc">
        8 位队长将通过拍卖竞价，从 A~E 五个位置池中签下选手组建战队
      </p>
      <ul class="rule-list">
        <li>每队每个位置仅可签下一名选手（含队长本人位置）</li>
        <li>管理员逐次选择要拍卖的位置池，每池开始前拖拽设定队长出价顺序</li>
        <li>确认出价顺序后随机抽签，再进入英式增价拍卖</li>
        <li>英式增价拍卖：出价须为 10 的倍数，须高于当前价且满足最低加价</li>
        <li>放弃后退出该选手的后续竞拍；其余人皆放弃时落槌成交</li>
        <li>一轮内无人加价则最高价者胜出；加价 10~100w，一口价仅首轮可用</li>
      </ul>
      <div class="captain-preview">
        <span v-for="c in captains" :key="c.name" class="cap-chip">
          {{ c.name }}
          <small>{{ c.funds }}w</small>
        </span>
      </div>
      <button class="btn-primary ceremony-btn" @click="emit('begin')">
        仪式开始
      </button>
      <a
        class="ref-link"
        href="https://www.bilibili.com/video/BV17mRkBXEK7/"
        target="_blank"
        rel="noopener"
      >
        参考：白菜杯 S4 选人仪式 ↗
      </a>
    </div>
  </div>

  <!-- 进入位置池 -->
  <div v-else-if="phase === 'pool_announce' && currentPool" class="overlay announce">
    <div class="overlay-card">
      <p class="eyebrow">位置池开启</p>
      <h2 class="pool-name">{{ POSITION_NAMES[currentPool] }}</h2>
      <p class="overlay-desc">
        第 {{ poolOrder.indexOf(currentPool) + 1 }} / {{ poolOrder.length }} 个位置池
      </p>
      <button class="btn-primary ceremony-btn" @click="emit('confirmPool')">
        进入拍卖
      </button>
    </div>
  </div>

  <!-- 抽签 -->
  <div v-else-if="phase === 'pool_draw'" class="overlay draw">
    <div class="overlay-bg draw-bg" aria-hidden="true" />
    <div class="draw-rays" aria-hidden="true" />
    <div class="overlay-card draw-card">
      <p class="eyebrow">随机选择程序</p>
      <div class="slot-frame" :class="{ spinning }">
        <div class="slot-scanline" />
        <PlayerAvatar
          v-if="revealedDrawPlayer && !spinning"
          :name="revealedDrawPlayer.name"
          :serial="revealedDrawPlayer.serial"
          :avatar="revealedDrawPlayer.avatar"
          :position="revealedDrawPlayer.position"
          size="xl"
          class="draw-avatar"
        />
        <h2 v-else class="spin-name" :class="{ spinning }">{{ spinName }}</h2>
      </div>
      <p class="overlay-desc">
        从 <strong>{{ POSITION_NAMES[currentPool!] }}</strong> 池
        {{ drawCandidates.length }} 名选手中抽取…
      </p>
      <div class="draw-dots">
        <span v-for="n in 3" :key="n" class="dot" :style="{ animationDelay: `${n * 0.2}s` }" />
      </div>
    </div>
  </div>

  <!-- 成交公布 -->
  <div v-else-if="phase === 'winner_reveal' && lastResult" class="overlay winner">
    <div class="overlay-bg winner-bg" aria-hidden="true" />
    <div v-if="lastResult.winner" class="confetti" aria-hidden="true">
      <span v-for="n in 12" :key="n" class="confetti-piece" :style="{ '--i': n }" />
    </div>
    <div class="overlay-card card-pop" :class="{ buyout: lastResult.buyout }">
      <PlayerAvatar
        :name="lastResult.player.name"
        :serial="lastResult.player.serial"
        :avatar="lastResult.player.avatar"
        :position="lastResult.player.position"
        size="xl"
        class="winner-avatar"
      />
      <p class="eyebrow">{{ lastResult.winner ? '签约成功' : '流拍' }}</p>
      <h2 class="overlay-title">{{ lastResult.player.name }}</h2>
      <p v-if="lastResult.winner" class="winner-line">
        <span class="winner-cap">{{ lastResult.winner }}</span>
        <span class="winner-price">{{ lastResult.price }}w</span>
      </p>
      <p v-else class="overlay-desc">本轮无人拍下</p>
      <button class="btn-primary ceremony-btn" @click="emit('confirmWinner')">
        继续
      </button>
    </div>
  </div>

  <!-- 最终阵容 -->
  <div v-else-if="phase === 'finished'" class="overlay finale">
    <div class="overlay-bg" aria-hidden="true" />
    <div class="overlay-card wide">
      <p class="eyebrow">仪式圆满落幕</p>
      <h2 class="overlay-title">最终阵容</h2>
      <div class="roster-grid">
        <div v-for="cap in captains" :key="cap.name" class="roster-card">
          <div class="roster-cap">{{ cap.name }}</div>
          <div class="roster-funds">剩余 {{ cap.funds }}w</div>
          <ul v-if="cap.team.length" class="roster-team">
            <li v-for="t in cap.team" :key="t">{{ t }}</li>
          </ul>
          <p v-else class="roster-empty">未签下选手</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(4, 8, 14, 0.72);
  backdrop-filter: blur(14px);
  animation: fadeIn 0.4s ease;
}

.overlay-bg {
  position: absolute;
  inset: 0;
  background:
    url('/images/hero-ceremony-bg.png') center / cover no-repeat;
  opacity: 0.35;
  animation: overlayPan 20s ease-in-out infinite alternate;
}

.overlay-bg.draw-bg {
  opacity: 0.42;
  filter: saturate(1.15) hue-rotate(-8deg);
}

.overlay-bg.winner-bg {
  opacity: 0.45;
  filter: saturate(1.2);
}

.overlay-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 70% 60% at 50% 40%, rgba(6, 10, 16, 0.35), rgba(4, 8, 14, 0.88)),
    url('/images/bg-texture.png') center / cover;
  opacity: 0.5;
  mix-blend-mode: overlay;
}

@keyframes overlayPan {
  from { transform: scale(1.05); }
  to { transform: scale(1.12); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes cardPop {
  from {
    opacity: 0;
    transform: scale(0.92) translateY(16px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.overlay-card {
  text-align: center;
  padding: 2.5rem 2rem;
  background:
    linear-gradient(160deg, rgba(14, 20, 32, 0.88), rgba(8, 12, 20, 0.82)),
    url('/images/bg-texture.png') center / cover;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  max-width: 480px;
  width: 90%;
  box-shadow: 0 32px 80px rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(20px);
  position: relative;
  z-index: 1;
}

.card-pop {
  animation: cardPop 0.45s cubic-bezier(0.34, 1.4, 0.64, 1);
}

.intro-logo {
  width: 72px;
  height: 72px;
  margin-bottom: 1rem;
  filter: drop-shadow(0 0 20px rgba(74, 222, 128, 0.5));
}

.overlay-card.wide {
  max-width: 900px;
  max-height: 80vh;
  overflow-y: auto;
}

.eyebrow {
  font-family: var(--font-display);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  color: var(--cabbage);
  margin-bottom: 0.5rem;
}

.overlay-title {
  font-family: var(--font-display);
  font-size: 2.1rem;
  font-weight: 800;
  margin-bottom: 0.75rem;
  background: linear-gradient(135deg, #fff, var(--gold-bright), var(--cabbage));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.pool-name {
  font-family: var(--font-display);
  font-size: 3rem;
  font-weight: 900;
  color: var(--gold);
  margin-bottom: 0.5rem;
  text-shadow: 0 0 40px rgba(245, 197, 66, 0.35);
}

.overlay-desc {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 1.25rem;
}

.overlay-desc strong {
  color: var(--gold);
}

.rule-list {
  text-align: left;
  list-style: none;
  margin: 1rem 0 1.25rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.rule-list li {
  padding: 0.35rem 0;
  padding-left: 1.1rem;
  position: relative;
}

.rule-list li::before {
  content: '›';
  position: absolute;
  left: 0;
  color: var(--cabbage);
  font-weight: 700;
}

.captain-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  justify-content: center;
  margin-bottom: 1.25rem;
}

.cap-chip {
  font-size: 0.75rem;
  padding: 0.3rem 0.65rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
  border-radius: 999px;
}

.cap-chip small {
  opacity: 0.6;
  margin-left: 0.25rem;
  color: var(--gold);
}

.ceremony-btn {
  padding: 0.7rem 2.25rem;
  font-size: 1rem;
}

.ref-link {
  display: block;
  margin-top: 1rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.2s;
}

.ref-link:hover {
  color: var(--cabbage);
}

.draw-rays {
  position: absolute;
  inset: 0;
  background:
    conic-gradient(from 0deg at 50% 50%, transparent 0deg, rgba(245, 197, 66, 0.04) 30deg, transparent 60deg);
  animation: rotateRays 8s linear infinite;
  pointer-events: none;
}

@keyframes rotateRays {
  to { transform: rotate(360deg); }
}

.draw-card {
  position: relative;
  z-index: 1;
  border-color: rgba(245, 197, 66, 0.25);
}

.slot-frame {
  position: relative;
  margin: 1rem 0;
  padding: 1.25rem 1.5rem;
  background: rgba(0, 0, 0, 0.35);
  border-radius: 14px;
  border: 2px solid var(--border);
  overflow: hidden;
}

.slot-frame.spinning {
  border-color: rgba(245, 197, 66, 0.45);
  box-shadow: 0 0 40px rgba(245, 197, 66, 0.15), inset 0 0 30px rgba(245, 197, 66, 0.05);
}

.slot-scanline {
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
  opacity: 0;
  animation: scan 1.2s ease-in-out infinite;
}

.slot-frame.spinning .slot-scanline {
  opacity: 0.6;
}

@keyframes scan {
  0% { top: 0; }
  100% { top: 100%; }
}

.draw-avatar {
  margin: 0.5rem auto;
}

.winner-avatar {
  margin: 0 auto 1rem;
}

.spin-name {
  font-family: var(--font-display);
  font-size: 2.75rem;
  font-weight: 800;
  color: var(--text);
  min-height: 3.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spin-name.spinning {
  color: var(--gold);
  animation: slotTick 0.08s ease infinite;
}

@keyframes slotTick {
  0%, 100% { transform: scaleY(1); }
  50% { transform: scaleY(0.95); opacity: 0.85; }
}

.draw-dots {
  display: flex;
  justify-content: center;
  gap: 0.4rem;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--gold);
  animation: dotPulse 1s ease infinite;
}

@keyframes dotPulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

.confetti {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.confetti-piece {
  position: absolute;
  width: 8px;
  height: 8px;
  top: -10px;
  left: calc(var(--i) * 8%);
  background: var(--gold);
  animation: confettiFall 2.5s ease-in forwards;
  animation-delay: calc(var(--i) * 0.1s);
  border-radius: 2px;
  opacity: 0.8;
}

.confetti-piece:nth-child(odd) {
  background: var(--cabbage);
  width: 6px;
  height: 10px;
}

@keyframes confettiFall {
  to {
    transform: translateY(100vh) rotate(720deg);
    opacity: 0;
  }
}

.winner .overlay-card.buyout {
  border-color: var(--gold);
  box-shadow: 0 0 60px rgba(245, 197, 66, 0.25);
}

.winner-line {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.winner-cap {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--green);
}

.winner-price {
  font-family: var(--font-display);
  font-size: 2.25rem;
  font-weight: 800;
  color: var(--gold);
  text-shadow: 0 0 20px rgba(245, 197, 66, 0.4);
}

.roster-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
  text-align: left;
}

.roster-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.85rem;
  transition: transform 0.2s ease;
}

.roster-card:hover {
  transform: translateY(-2px);
}

.roster-cap {
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.roster-funds {
  font-size: 0.75rem;
  color: var(--gold);
  margin-bottom: 0.5rem;
}

.roster-team {
  list-style: none;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.roster-team li {
  padding: 0.15rem 0;
}

.roster-empty {
  font-size: 0.75rem;
  color: var(--text-muted);
  opacity: 0.6;
}
</style>
