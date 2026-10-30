<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { POSITION_COLORS, POSITION_SHORT } from '../constants'
import { fetchAuctionHistory, type AuctionHistoryRecord } from '../api/auction'
import type { Position } from '../types'

const records = ref<AuctionHistoryRecord[]>([])
const selectedId = ref('')
const loading = ref(true)
const error = ref('')
const selected = computed(() => records.value.find((record) => record.id === selectedId.value) ?? records.value[0] ?? null)
const soldCount = computed(() => selected.value?.state.players.filter((player) => player.sold).length ?? 0)
const unsoldCount = computed(() => selected.value ? selected.value.state.players.length - soldCount.value : 0)
const eventCount = computed(() => selected.value?.state.logs.length ?? 0)

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

function positionFor(name: string): Position | null {
  return selected.value?.state.players.find((player) => player.name === name)?.position ?? null
}
</script>

<template>
  <div class="history-page">
    <header class="history-head">
      <div class="head-copy">
        <p class="eyebrow"><span class="eyebrow-dot" /> BAICAI CUP · S6 ARCHIVE</p>
        <h1>拍卖记录</h1>
        <p class="head-description">从第一轮叫价到最终阵容，完整回看每一次落槌。</p>
      </div>
      <div class="head-actions">
        <label class="archive-select">
          <span>场次记录</span>
          <select v-model="selectedId" :disabled="!records.length">
            <option v-for="record in records" :key="record.id" :value="record.id">
              {{ formatTime(record.completedAt) }}
            </option>
          </select>
        </label>
        <RouterLink class="return-link" to="/spectator"><span aria-hidden="true">←</span> 观战大屏</RouterLink>
      </div>
    </header>

    <p v-if="loading" class="state-message">正在读取已归档的场次…</p>
    <p v-else-if="error" class="state-message state-error">{{ error }}</p>
    <p v-else-if="!records.length" class="state-message">暂无已完成的拍卖记录。仪式结束后会自动归档。</p>

    <template v-else-if="selected">
      <section class="summary-strip" aria-label="本场拍卖统计">
        <article class="summary-item">
          <span class="summary-label">成交选手</span>
          <strong>{{ soldCount }}</strong>
          <span class="summary-unit">人</span>
        </article>
        <article class="summary-item">
          <span class="summary-label">未成交</span>
          <strong>{{ unsoldCount }}</strong>
          <span class="summary-unit">人</span>
        </article>
        <article class="summary-item">
          <span class="summary-label">流程节点</span>
          <strong>{{ eventCount }}</strong>
          <span class="summary-unit">条记录</span>
        </article>
        <div class="summary-date">
          <span>归档时间</span>
          <strong>{{ formatTime(selected.completedAt) }}</strong>
        </div>
      </section>

      <div class="archive-layout">
        <section class="teams-section">
          <div class="section-heading">
            <div>
              <p class="section-kicker">FINAL ROSTERS</p>
              <h2>最终阵容</h2>
            </div>
            <span class="section-count">{{ selected.state.captains.length }} 支队伍</span>
          </div>

          <div class="teams-grid">
            <article v-for="(captain, index) in selected.state.captains" :key="captain.name" class="team-card">
              <header class="team-head">
                <div class="team-identity">
                  <span class="team-index">{{ String(index + 1).padStart(2, '0') }}</span>
                  <div>
                    <span class="captain-label">队长</span>
                    <h3>{{ captain.name }}</h3>
                  </div>
                </div>
                <div class="funds"><span>剩余资金</span><strong>{{ captain.funds }}<small>w</small></strong></div>
              </header>
              <ul v-if="captain.team.length" class="player-list">
                <li v-for="name in captain.team" :key="name">
                  <span class="position-tag" :style="{ '--position-color': positionFor(name) ? POSITION_COLORS[positionFor(name)!] : '#a59a8e' }">
                    {{ positionFor(name) ? POSITION_SHORT[positionFor(name)!] : '选手' }}
                  </span>
                  <span class="player-name">{{ name }}</span>
                </li>
              </ul>
              <p v-else class="empty-team">本场未签下选手</p>
            </article>
          </div>
        </section>

        <section class="timeline-section">
          <header class="timeline-head">
            <div>
              <p class="section-kicker">PLAY BY PLAY</p>
              <h2>完整流程</h2>
            </div>
            <span class="event-count">{{ eventCount }} 条</span>
          </header>
          <ol class="timeline">
            <li v-for="entry in selected.state.logs" :key="entry.id" :class="entry.type" class="timeline-entry">
              <time>{{ entry.time }}</time>
              <span class="event-text">{{ entry.text }}</span>
            </li>
          </ol>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.history-page {
  --paper: #f6f3ed;
  --surface: #fffefa;
  --ink: #302b26;
  --muted: #81776e;
  --line: #e8e1d7;
  --terracotta: #b85c3f;
  --terracotta-soft: #f5e7df;
  width: 100%;
  color: var(--ink);
}

.history-head { display: flex; justify-content: space-between; align-items: end; gap: 2rem; padding: .8rem .2rem 1.5rem; }
.eyebrow, .section-kicker { color: var(--terracotta); font: 700 .66rem/1.3 var(--font-display); letter-spacing: .15em; }
.eyebrow { display: flex; align-items: center; gap: .5rem; }
.eyebrow-dot { width: .42rem; height: .42rem; border-radius: 50%; background: var(--terracotta); }
.history-head h1 { margin-top: .55rem; font: 600 clamp(2rem, 3vw, 2.6rem)/1.15 Georgia, 'Songti SC', 'Noto Serif SC', serif; letter-spacing: -.035em; }
.head-description { margin-top: .55rem; color: var(--muted); font-size: .92rem; }
.head-actions { display: flex; align-items: end; gap: .65rem; }
.archive-select { display: grid; gap: .35rem; color: var(--muted); font-size: .72rem; font-weight: 650; }
.archive-select select { min-width: 15.5rem; height: 2.65rem; padding: 0 2.2rem 0 .8rem; color: var(--ink); background: var(--surface); border: 1px solid var(--line); border-radius: 9px; font: 500 .8rem var(--font); }
.return-link { display: inline-flex; align-items: center; gap: .4rem; height: 2.65rem; padding: 0 .85rem; color: var(--ink); border: 1px solid var(--line); border-radius: 9px; text-decoration: none; background: var(--surface); font-size: .8rem; font-weight: 650; white-space: nowrap; }
.return-link:hover { border-color: #d9ad99; color: var(--terracotta); }
.state-message { margin: 1rem 0; padding: 1.1rem 1.25rem; border: 1px solid var(--line); border-radius: 12px; background: var(--surface); color: var(--muted); }
.state-error { color: #a33b2d; }

.summary-strip { display: grid; grid-template-columns: repeat(3, minmax(8rem, .72fr)) minmax(13rem, 1.55fr); align-items: stretch; margin-bottom: 1.4rem; border: 1px solid var(--line); border-radius: 13px; background: var(--surface); box-shadow: 0 4px 16px rgba(64, 45, 29, .035); }
.summary-item { display: grid; grid-template-columns: auto auto; justify-content: center; align-content: center; align-items: baseline; column-gap: .35rem; padding: .85rem 1rem; border-right: 1px solid var(--line); }
.summary-label { grid-column: 1 / -1; margin-bottom: .15rem; color: var(--muted); font-size: .72rem; }
.summary-item strong { color: var(--ink); font: 600 1.65rem/1.2 Georgia, 'Times New Roman', serif; font-variant-numeric: tabular-nums; }
.summary-unit { color: var(--muted); font-size: .7rem; }
.summary-date { display: flex; flex-direction: column; justify-content: center; gap: .2rem; padding: .8rem 1.2rem; }
.summary-date span { color: var(--muted); font-size: .7rem; }
.summary-date strong { color: var(--ink); font-size: .82rem; font-weight: 650; font-variant-numeric: tabular-nums; }

.archive-layout { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(340px, .8fr); gap: 1.2rem; align-items: start; }
.teams-section, .timeline-section { min-width: 0; }
.section-heading, .timeline-head { display: flex; justify-content: space-between; align-items: end; gap: 1rem; margin: 0 0 .75rem; }
.section-heading h2, .timeline-head h2 { margin-top: .18rem; font: 600 1.35rem/1.25 Georgia, 'Songti SC', 'Noto Serif SC', serif; letter-spacing: -.02em; }
.section-count, .event-count { color: var(--muted); font-size: .76rem; }
.teams-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .7rem; }
.team-card { min-width: 0; padding: .85rem .95rem; border: 1px solid var(--line); border-radius: 12px; background: var(--surface); box-shadow: 0 3px 12px rgba(64, 45, 29, .025); transition: border-color .18s, transform .18s; }
.team-card:hover { border-color: #d8b8a9; transform: translateY(-1px); }
.team-head { display: flex; justify-content: space-between; align-items: center; gap: .6rem; padding-bottom: .65rem; border-bottom: 1px solid #f0ebe4; }
.team-identity { display: flex; align-items: center; gap: .65rem; min-width: 0; }
.team-index { display: grid; place-items: center; flex: 0 0 2rem; width: 2rem; height: 2rem; border-radius: 8px; background: var(--terracotta-soft); color: var(--terracotta); font: 700 .68rem var(--font-display); }
.captain-label, .funds span { display: block; color: var(--muted); font-size: .64rem; }
.team-identity h3 { margin-top: .08rem; color: var(--ink); font-size: .9rem; font-weight: 700; overflow-wrap: anywhere; }
.funds { flex: 0 0 auto; text-align: right; }
.funds strong { display: block; margin-top: .05rem; color: var(--ink); font: 650 .92rem var(--font-display); font-variant-numeric: tabular-nums; }
.funds small { margin-left: .1rem; color: var(--muted); font-size: .65rem; }
.player-list { display: grid; gap: .25rem; padding-top: .58rem; list-style: none; }
.player-list li { display: flex; min-width: 0; align-items: center; gap: .55rem; min-height: 1.65rem; }
.position-tag { display: inline-grid; place-items: center; flex: 0 0 2.05rem; height: 1.25rem; color: var(--position-color); border: 1px solid color-mix(in srgb, var(--position-color) 28%, white); border-radius: 5px; background: color-mix(in srgb, var(--position-color) 9%, white); font: 700 .58rem var(--font-display); }
.player-name { min-width: 0; color: #4d453e; font-size: .75rem; line-height: 1.35; overflow-wrap: anywhere; }
.empty-team { padding-top: .6rem; color: var(--muted); font-size: .78rem; }
.timeline-section { position: sticky; top: 1rem; padding: .95rem; border: 1px solid var(--line); border-radius: 13px; background: var(--surface); box-shadow: 0 4px 16px rgba(64, 45, 29, .035); }
.timeline-head { align-items: center; margin: 0; padding: 0 .15rem .75rem; border-bottom: 1px solid var(--line); }
.timeline { display: grid; max-height: min(67vh, 54rem); gap: 0; padding: .35rem .1rem 0; overflow: auto; list-style: none; scrollbar-color: #d7cfc4 transparent; scrollbar-width: thin; }
.timeline-entry { display: grid; grid-template-columns: 3.75rem minmax(0, 1fr); gap: .55rem; padding: .55rem .35rem; border-bottom: 1px solid #f2eee8; border-left: 2px solid transparent; }
.timeline-entry:last-child { border-bottom: 0; }
.timeline time { padding-top: .05rem; color: #94887d; font: 600 .65rem/1.5 var(--font-display); font-variant-numeric: tabular-nums; }
.event-text { color: #5b524a; font-size: .73rem; line-height: 1.5; overflow-wrap: anywhere; }
.timeline-entry.bid, .timeline-entry.buyout { border-left-color: #d59a59; }
.timeline-entry.win { border-left-color: #718f70; }
.timeline-entry.warn { border-left-color: #c97b69; }

@media (max-width: 1000px) {
  .archive-layout { grid-template-columns: minmax(0, 1fr); }
  .timeline-section { position: static; }
  .timeline { max-height: 60vh; }
}
@media (max-width: 680px) {
  .history-head { align-items: start; flex-direction: column; gap: 1rem; }
  .head-actions { width: 100%; align-items: end; }
  .archive-select { flex: 1; min-width: 0; }
  .archive-select select { width: 100%; min-width: 0; }
  .summary-strip { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .summary-item { padding: .7rem .45rem; }
  .summary-date { grid-column: 1 / -1; padding: .65rem .85rem; border-top: 1px solid var(--line); }
  .teams-grid { grid-template-columns: minmax(0, 1fr); }
  .timeline { max-height: none; }
}
@media (max-width: 420px) {
  .head-actions { align-items: stretch; flex-direction: column; }
  .return-link { justify-content: center; }
  .timeline-entry { grid-template-columns: 3.25rem minmax(0, 1fr); gap: .35rem; }
}
</style>
