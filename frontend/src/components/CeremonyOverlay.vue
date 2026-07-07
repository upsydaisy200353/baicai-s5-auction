<script setup lang="ts">
import { computed, ref, watch, onUnmounted } from 'vue'
import { POSITION_COLORS, POSITION_NAMES } from '../constants'
import { playSound, unlockAudio } from '../lib/soundEngine'
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
  revealDraw: []
  confirmWinner: []
  drawTick: []
}>()

const carouselIndex = ref(0)
const spinning = ref(false)
let spinTimer: ReturnType<typeof setInterval> | null = null

const currentCarouselPlayer = computed(() => {
  const list = props.drawCandidates
  if (!list.length) return null
  return list[carouselIndex.value % list.length]!
})

const poolColor = computed(() =>
  props.currentPool ? POSITION_COLORS[props.currentPool] : 'var(--purple)',
)

function startCarousel() {
  const list = props.drawCandidates
  if (!list.length) {
    if (props.isAdmin) emit('revealDraw')
    return
  }

  stopCarousel()
  spinning.value = true
  carouselIndex.value = 0
  let tick = 0
  const totalTicks = 28

  spinTimer = setInterval(() => {
    carouselIndex.value = (carouselIndex.value + 1) % list.length
    tick++
    if (tick % 4 === 0) emit('drawTick')
    if (tick >= totalTicks) {
      stopCarousel()
      if (props.isAdmin) emit('revealDraw')
    }
  }, 80)
}

function stopCarousel() {
  if (spinTimer) clearInterval(spinTimer)
  spinTimer = null
  spinning.value = false
}

function onBegin() {
  void unlockAudio()
  playSound('uiClick')
  emit('begin')
}

function onConfirmWinner() {
  void unlockAudio()
  playSound('uiClick')
  emit('confirmWinner')
}

watch(
  () => [props.phase, props.drawCandidates.length] as const,
  ([phase]) => {
    if (phase === 'pool_draw') {
      if (!spinning.value && !spinTimer) {
        setTimeout(startCarousel, 400)
      }
    } else {
      stopCarousel()
      carouselIndex.value = 0
    }
  },
  { immediate: true },
)

onUnmounted(stopCarousel)
</script>

<template>
  <!-- 开场 -->
  <div v-if="phase === 'intro'" class="overlay intro">
    <div class="overlay-bg" aria-hidden="true" />
    <div class="overlay-card card-pop">
      <img src="/logo.svg" alt="" class="intro-logo" />
      <p class="eyebrow">BAICAI CUP · LIVE AUCTION</p>
      <h2 class="overlay-title">公开叫价选人仪式</h2>
      <p class="overlay-desc">英式增价拍卖 · 全员同时叫价 · 倒计时落槌</p>
      <ul class="rule-list">
        <li>管理员逐次选择位置池，每池随机抽出一名选手</li>
        <li>所有队长<strong>同时</strong>公开叫价，价高者得</li>
        <li>每次加价后重置 <strong>45 秒</strong>倒计时；无人继续加价则落槌</li>
        <li>每次加价至少 <strong>10w</strong>；支持一口价秒拍（每位队长整场仅一次）</li>
        <li>若<strong>60 秒</strong>内尚无人出价则流拍（管理员可调整计时）</li>
        <li>每队每个位置仅可签下一名选手（含队长本人位置）</li>
      </ul>
      <div class="captain-preview">
        <span v-for="c in captains" :key="c.name" class="cap-chip">
          {{ c.name }}
          <small>{{ c.funds }}w</small>
        </span>
      </div>
      <button class="btn-primary ceremony-btn" @click="onBegin">进入仪式</button>
    </div>
  </div>

  <!-- 抽取标的 -->
  <div v-else-if="phase === 'pool_draw'" class="overlay draw">
    <div class="overlay-bg draw-bg" aria-hidden="true" />
    <div class="draw-rays" aria-hidden="true" />
    <div class="overlay-card draw-card">
      <p class="eyebrow">抽取拍卖标的</p>
      <div class="slot-frame" :class="{ spinning }" :style="{ '--pool-color': poolColor }">
        <div v-if="currentCarouselPlayer" class="carousel-slot" :class="{ spinning }">
          <PlayerAvatar
            :name="currentCarouselPlayer.name"
            :serial="currentCarouselPlayer.serial"
            :avatar="currentCarouselPlayer.avatar"
            :position="currentCarouselPlayer.position"
            size="xl"
            class="carousel-avatar"
          />
          <p class="carousel-serial">{{ currentCarouselPlayer.serial }}</p>
          <h2 class="carousel-name">{{ currentCarouselPlayer.name }}</h2>
        </div>
        <p v-else class="carousel-empty">该池暂无候选选手</p>
      </div>
      <p class="overlay-desc">
        从 <strong>{{ POSITION_NAMES[currentPool!] }}</strong> 池
        {{ drawCandidates.length }} 名候选中抽取标的…
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
    <div class="overlay-card card-pop">
      <PlayerAvatar
        :name="lastResult.player.name"
        :serial="lastResult.player.serial"
        :avatar="lastResult.player.avatar"
        :position="lastResult.player.position"
        size="xl"
        class="winner-avatar"
      />
      <p class="eyebrow">{{ lastResult.winner ? '落槌成交' : '流拍' }}</p>
      <h2 v-if="lastResult.winner" class="overlay-title winner-announce">
        由 <span class="winner-cap">{{ lastResult.winner }}</span> 队长拍得
        <span class="winner-player">{{ lastResult.player.name }}</span>
      </h2>
      <h2 v-else class="overlay-title">{{ lastResult.player.name }}</h2>
      <p v-if="lastResult.winner" class="winner-price-line">{{ lastResult.price }}w</p>
      <p v-else class="overlay-desc">本轮无人拍下</p>
      <button v-if="isAdmin" class="btn-primary ceremony-btn" @click="onConfirmWinner">
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
  background: url('/images/hero-ceremony-bg.png') center / cover no-repeat;
  opacity: 0.35;
}

.overlay-bg.draw-bg {
  opacity: 0.42;
  filter: saturate(1.15) hue-rotate(20deg);
}

.overlay-bg.winner-bg {
  opacity: 0.45;
}

.overlay-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 70% 60% at 50% 40%, rgba(6, 10, 16, 0.35), rgba(4, 8, 14, 0.88));
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes cardPop {
  from { opacity: 0; transform: scale(0.92) translateY(16px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.overlay-card {
  text-align: center;
  padding: 2.5rem 2rem;
  background: linear-gradient(160deg, rgba(14, 20, 32, 0.88), rgba(8, 12, 20, 0.82));
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  max-width: 480px;
  width: 90%;
  box-shadow: 0 32px 80px rgba(0, 0, 0, 0.55);
  position: relative;
  z-index: 1;
}

.card-pop { animation: cardPop 0.45s cubic-bezier(0.34, 1.4, 0.64, 1); }

.overlay-card.wide {
  max-width: 560px;
  max-height: 80vh;
  overflow-y: auto;
}

.intro-logo {
  width: 72px;
  height: 72px;
  margin-bottom: 1rem;
  filter: drop-shadow(0 0 20px rgba(168, 85, 247, 0.5));
}

.eyebrow {
  font-family: var(--font-display);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  color: #c084fc;
  margin-bottom: 0.5rem;
}

.overlay-title {
  font-family: var(--font-display);
  font-size: 2.1rem;
  font-weight: 800;
  margin-bottom: 0.75rem;
  background: linear-gradient(135deg, #fff, #c084fc, var(--gold-bright));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.overlay-desc {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 1.25rem;
}

.overlay-desc strong { color: var(--gold); }

.rule-list {
  text-align: left;
  list-style: none;
  margin: 1rem 0 1.25rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.rule-list li {
  padding: 0.35rem 0 0.35rem 1.1rem;
  position: relative;
}

.rule-list li::before {
  content: '›';
  position: absolute;
  left: 0;
  color: #c084fc;
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

.draw-rays {
  position: absolute;
  inset: 0;
  background: conic-gradient(from 0deg at 50% 50%, transparent 0deg, rgba(168, 85, 247, 0.06) 30deg, transparent 60deg);
  animation: rotateRays 8s linear infinite;
  pointer-events: none;
}

@keyframes rotateRays { to { transform: rotate(360deg); } }

.draw-card { border-color: rgba(168, 85, 247, 0.25); }

.slot-frame {
  position: relative;
  margin: 1rem 0;
  padding: 1.25rem 1.5rem;
  background: rgba(0, 0, 0, 0.35);
  border-radius: 14px;
  border: 2px solid var(--border);
}

.slot-frame.spinning {
  border-color: color-mix(in srgb, var(--pool-color) 55%, transparent);
  box-shadow: 0 0 40px color-mix(in srgb, var(--pool-color) 25%, transparent);
}

.carousel-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  min-height: 200px;
  justify-content: center;
}

.carousel-slot.spinning .carousel-avatar {
  animation: carouselPulse 0.08s ease infinite;
}

.carousel-slot.spinning .carousel-name {
  animation: slotTick 0.08s ease infinite;
}

@keyframes carouselPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(0.97); opacity: 0.92; }
}

.carousel-serial {
  font-family: var(--font-display);
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--pool-color, var(--accent));
  margin-top: 0.5rem;
}

.carousel-name {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 800;
  min-height: 2.2rem;
  color: var(--text);
}

.carousel-empty {
  padding: 2rem 1rem;
  color: var(--text-muted);
  font-size: 0.9rem;
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
  background: #c084fc;
  animation: dotPulse 1s ease infinite;
}

@keyframes dotPulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

.winner-avatar { margin: 0 auto 1rem; }

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
}

@keyframes confettiFall {
  to { transform: translateY(100vh) rotate(720deg); opacity: 0; }
}

.winner-announce {
  font-size: 1.65rem;
  line-height: 1.45;
}

.winner-player {
  display: block;
  margin-top: 0.35rem;
  font-size: 2rem;
  background: linear-gradient(135deg, #fff, var(--gold-bright));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.winner-price-line {
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--gold);
  margin-bottom: 1.25rem;
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
}

.roster-cap { font-weight: 700; margin-bottom: 0.25rem; }
.roster-funds { font-size: 0.75rem; color: var(--gold); margin-bottom: 0.5rem; }
.roster-team { list-style: none; font-size: 0.75rem; color: var(--text-muted); }
.roster-empty { font-size: 0.75rem; color: var(--text-muted); opacity: 0.6; }
</style>
