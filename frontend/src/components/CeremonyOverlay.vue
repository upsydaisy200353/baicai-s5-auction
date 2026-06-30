<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { POSITION_NAMES } from '../constants'
import type { Captain, LastResult, Player, Position } from '../types'

const props = defineProps<{
  phase: string
  captains: Captain[]
  currentPool: Position | null
  poolOrder: Position[]
  drawCandidates: Player[]
  lastResult: LastResult | null
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
      emit('revealDraw')
    }
  }, 80)
}

function stopSpin() {
  if (spinTimer) clearInterval(spinTimer)
  spinTimer = null
  spinning.value = false
}

watch(
  () => props.phase,
  (phase) => {
    if (phase === 'pool_draw' && props.drawCandidates.length) {
      spinName.value = '???'
      setTimeout(startSpin, 400)
    }
  },
)

onUnmounted(stopSpin)
</script>

<template>
  <!-- 开场 -->
  <div v-if="phase === 'intro'" class="overlay intro">
    <div class="overlay-card">
      <p class="eyebrow">白菜杯 S5</p>
      <h2 class="overlay-title">选人仪式</h2>
      <p class="overlay-desc">
        8 位队长将通过拍卖竞价，从 A~E 五个位置池中签下选手组建战队
      </p>
      <ul class="rule-list">
        <li>每队每个位置仅可签下一名选手（含队长本人位置）</li>
        <li>管理员确定五个位置池的拍卖顺序</li>
        <li>管理员可设定队长出价先后</li>
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
    <div class="overlay-card">
      <p class="eyebrow">随机选择程序</p>
      <h2 class="spin-name" :class="{ spinning }">{{ spinName }}</h2>
      <p class="overlay-desc">
        从 {{ POSITION_NAMES[currentPool!] }} 池 {{ drawCandidates.length }} 名选手中抽取…
      </p>
    </div>
  </div>

  <!-- 成交公布 -->
  <div v-else-if="phase === 'winner_reveal' && lastResult" class="overlay winner">
    <div class="overlay-card" :class="{ buyout: lastResult.buyout }">
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
  background: rgba(8, 12, 20, 0.88);
  backdrop-filter: blur(8px);
  animation: fadeIn 0.35s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.overlay-card {
  text-align: center;
  padding: 2.5rem 2rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  max-width: 480px;
  width: 90%;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.5);
}

.overlay-card.wide {
  max-width: 900px;
  max-height: 80vh;
  overflow-y: auto;
}

.eyebrow {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--accent);
  margin-bottom: 0.5rem;
}

.overlay-title {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 0.75rem;
  background: linear-gradient(90deg, var(--gold), #fde68a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.pool-name {
  font-size: 3rem;
  font-weight: 900;
  color: var(--gold);
  margin-bottom: 0.5rem;
}

.overlay-desc {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 1.25rem;
}

.rule-list {
  text-align: left;
  list-style: none;
  margin: 1rem 0 1.25rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.rule-list li {
  padding: 0.3rem 0;
  padding-left: 1rem;
  position: relative;
}

.rule-list li::before {
  content: '›';
  position: absolute;
  left: 0;
  color: var(--accent);
}

.captain-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  justify-content: center;
  margin-bottom: 1.25rem;
}

.cap-chip {
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  background: var(--bg-hover);
  border-radius: 999px;
}

.cap-chip small {
  opacity: 0.6;
  margin-left: 0.25rem;
}

.ceremony-btn {
  padding: 0.65rem 2rem;
  font-size: 1rem;
}

.ref-link {
  display: block;
  margin-top: 1rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  text-decoration: none;
}

.ref-link:hover {
  color: var(--accent);
}

.spin-name {
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--text);
  margin: 1rem 0;
  min-height: 3rem;
}

.spin-name.spinning {
  color: var(--gold);
  animation: glow 0.4s ease infinite alternate;
}

@keyframes glow {
  from { text-shadow: 0 0 8px var(--gold-dim); }
  to { text-shadow: 0 0 24px var(--gold); }
}

.winner .overlay-card.buyout {
  border-color: var(--gold);
  box-shadow: 0 0 40px var(--gold-dim);
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
  font-size: 2rem;
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
  background: var(--bg-hover);
  border-radius: 8px;
  padding: 0.75rem;
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
