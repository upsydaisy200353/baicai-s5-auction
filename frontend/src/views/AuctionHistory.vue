<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchAuctionHistory, type AuctionHistoryRecord } from '../api/auction'

const records = ref<AuctionHistoryRecord[]>([])
const selectedId = ref('')
const loading = ref(true)
const error = ref('')
const selected = computed(() => records.value.find((record) => record.id === selectedId.value) ?? records.value[0] ?? null)

onMounted(async () => {
  try {
    records.value = await fetchAuctionHistory()
    selectedId.value = records.value[0]?.id ?? ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : '历史记录加载失败'
  } finally {
    loading.value = false
  }
})

function formatTime(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN', { hour12: false })
}
</script>

<template>
  <div class="history-page">
    <header class="history-head card">
      <div>
        <p class="eyebrow">AUCTION ARCHIVE</p>
        <h1>拍卖历史</h1>
        <p>仪式结束后自动保存完整操作记录与最终阵容。</p>
      </div>
      <RouterLink class="btn-ghost" to="/spectator">返回观战大屏</RouterLink>
    </header>

    <p v-if="loading" class="notice">正在加载历史记录…</p>
    <p v-else-if="error" class="notice error">{{ error }}</p>
    <p v-else-if="!records.length" class="notice">暂无已完成的拍卖记录。仪式结束后会自动归档。</p>

    <template v-else-if="selected">
      <section class="record-picker card">
        <label for="auction-record">选择场次</label>
        <select id="auction-record" v-model="selectedId">
          <option v-for="record in records" :key="record.id" :value="record.id">
            {{ formatTime(record.completedAt) }} · {{ record.state.players.filter((p) => p.sold).length }} 人成交
          </option>
        </select>
      </section>

      <section class="teams-section">
        <h2>最终阵容</h2>
        <div class="teams-grid">
          <article v-for="captain in selected.state.captains" :key="captain.name" class="team-card card">
            <div class="team-head">
              <h3>{{ captain.name }}</h3>
              <span>剩余 {{ captain.funds }}w</span>
            </div>
            <ul v-if="captain.team.length">
              <li v-for="name in captain.team" :key="name">{{ name }}</li>
            </ul>
            <p v-else class="empty-team">本场未签下选手</p>
          </article>
        </div>
      </section>

      <section class="timeline-section card">
        <h2>完整流程</h2>
        <ol class="timeline">
          <li v-for="entry in selected.state.logs" :key="entry.id" :class="entry.type">
            <time>{{ entry.time }}</time>
            <span>{{ entry.text }}</span>
          </li>
        </ol>
      </section>
    </template>
  </div>
</template>

<style scoped>
.history-page { width: 100%; display: grid; gap: 1rem; }
.history-head { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; padding: 1.2rem 1.35rem; }
.eyebrow { color: var(--gold); font-size: .68rem; letter-spacing: .15em; font-family: var(--font-display); }
.history-head h1 { font-size: 1.5rem; font-weight: 800; }
.history-head p:last-child { margin-top: .3rem; color: var(--text-muted); font-size: .86rem; }
.notice { padding: 1rem 1.2rem; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); color: var(--text-muted); }
.notice.error { color: var(--red); }
.record-picker { display: flex; align-items: center; gap: .8rem; flex-wrap: wrap; padding: 1rem 1.2rem; }
.record-picker label { color: var(--text-muted); font-weight: 700; }
.record-picker select { min-width: min(100%, 26rem); padding: .65rem .8rem; color: var(--text); background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); }
.teams-section h2, .timeline-section h2 { margin: 0 0 .75rem; font-size: 1.1rem; font-weight: 800; }
.teams-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr)); gap: .75rem; }
.team-card { padding: 1rem 1.1rem; }
.team-head { display: flex; justify-content: space-between; gap: .6rem; align-items: baseline; }
.team-head h3 { font-weight: 800; color: var(--gold-bright); }
.team-head span, .empty-team { color: var(--text-muted); font-size: .78rem; }
.team-card ul { margin: .65rem 0 0; padding-left: 1.1rem; color: var(--text); line-height: 1.7; }
.empty-team { margin-top: .6rem; }
.timeline-section { padding: 1.1rem 1.2rem; }
.timeline { list-style: none; display: grid; gap: .45rem; max-height: 70vh; overflow: auto; }
.timeline li { display: grid; grid-template-columns: 4.5rem minmax(0, 1fr); gap: .7rem; padding: .48rem .6rem; border-left: 2px solid var(--border); border-radius: 0 .35rem .35rem 0; background: rgba(255,255,255,.025); }
.timeline time { color: var(--text-muted); font-variant-numeric: tabular-nums; font-size: .8rem; }
.timeline span { overflow-wrap: anywhere; line-height: 1.5; }
.timeline .bid, .timeline .buyout { border-left-color: var(--gold); }
.timeline .win { border-left-color: var(--cabbage); }
.timeline .warn { border-left-color: var(--red); }
@media (max-width: 600px) { .timeline li { grid-template-columns: 1fr; gap: .2rem; } }
</style>
