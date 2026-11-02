<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { POSITION_COLORS, POSITION_SHORT, POSITION_NAMES } from '../constants'
import { fetchAuctionHistory, type AuctionHistoryRecord } from '../api/auction'
import type { Position } from '../types'

const POSITION_ORDER: Position[] = ['Top', 'Jungle', 'Mid', 'Bot', 'Support']

const records = ref<AuctionHistoryRecord[]>([])
const selectedId = ref('')
const loading = ref(true)
const error = ref('')
const selected = computed(() => records.value.find((record) => record.id === selectedId.value) ?? records.value[0] ?? null)
const soldCount = computed(() => selected.value?.state.players.filter((player) => player.sold).length ?? 0)
const unsoldCount = computed(() => selected.value ? selected.value.state.players.length - soldCount.value : 0)
const flowedPlayers = computed(() =>
  selected.value?.state.players.filter((player) => !player.sold && (player.excluded || player.inUnsoldPool)) ?? [],
)
const flowedGroups = computed(() =>
  POSITION_ORDER
    .map((position) => ({
      position,
      players: flowedPlayers.value.filter((player) => player.position === position),
    }))
    .filter((group) => group.players.length > 0),
)
const eventCount = computed(() => selected.value?.state.logs.length ?? 0)
const playerSearch = ref('')
const selectedPlayerSerial = ref('')
const searchablePlayers = computed(() => {
  const players = selected.value?.state.players ?? []
  const query = playerSearch.value.trim().toLocaleLowerCase()
  return players
    .filter((player) => !query || `${player.name} ${player.serial}`.toLocaleLowerCase().includes(query))
    .slice(0, 8)
})
const selectedPlayer = computed(() =>
  selected.value?.state.players.find((player) => player.serial === selectedPlayerSerial.value) ?? null,
)
const playerRounds = computed(() => {
  const player = selectedPlayer.value
  const logs = selected.value?.state.logs ?? []
  if (!player) return []

  const rounds: { stage: string; entries: typeof logs }[] = []
  let active: { stage: string; entries: typeof logs } | null = null
  const marker = `公开竞拍 — ${player.serial} ${player.name} ·`

  for (const entry of logs) {
    if (entry.text.startsWith('公开竞拍 — ')) {
      if (active?.entries.length) rounds.push(active)
      active = entry.text.startsWith(marker)
        ? { stage: rounds.length ? '流拍池重拍' : '正式竞拍', entries: [entry] }
        : null
      continue
    }
    if (!active) continue
    active.entries.push(entry)
    if (
      entry.type === 'win' ||
      entry.text.startsWith(`流拍：${player.name} —`) ||
      entry.text.startsWith(`二次拍卖流拍：${player.name} —`)
    ) {
      rounds.push(active)
      active = null
    }
  }
  if (active?.entries.length) rounds.push(active)
  return rounds
})

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
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN', { hour12: false, timeZone: 'Asia/Shanghai' })
}

function formatLogTime(value: string) {
  const match = value.match(/^(\d{1,2}):(\d{2}):(\d{2})$/)
  if (!match) {
    const date = new Date(value)
    return Number.isNaN(date.getTime()) ? value : date.toLocaleTimeString('zh-CN', { hour12: false, timeZone: 'Asia/Shanghai' })
  }
  const total = (Number(match[1]) * 3600 + Number(match[2]) * 60 + Number(match[3]) + 8 * 3600) % 86400
  return [Math.floor(total / 3600), Math.floor((total % 3600) / 60), total % 60]
    .map((part) => String(part).padStart(2, '0'))
    .join(':')
}

function playerFor(name: string) {
  return selected.value?.state.players.find((player) => player.name === name) ?? null
}

function positionFor(name: string): Position | null {
  return playerFor(name)?.position ?? null
}

function orderedTeam(names: string[]) {
  return [...names].sort((left, right) => {
    const leftPosition = playerFor(left)?.position
    const rightPosition = playerFor(right)?.position
    return POSITION_ORDER.indexOf(leftPosition ?? 'Support') - POSITION_ORDER.indexOf(rightPosition ?? 'Support')
  })
}

function priceFor(name: string) {
  return playerFor(name)?.finalPrice ?? null
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

      <section class="player-process" aria-label="选手竞拍流程查询">
        <div class="process-heading">
          <div>
            <p class="section-kicker">PLAYER BID HISTORY</p>
            <h2>选手竞拍流程</h2>
            <p>搜索选手，查看每轮起拍、队长出价与最终结果。</p>
          </div>
          <span v-if="selectedPlayer" class="process-player-position">{{ selectedPlayer.position }}</span>
        </div>
        <label class="player-search">
          <span class="search-icon" aria-hidden="true">⌕</span>
          <input v-model="playerSearch" @input="selectedPlayerSerial = ''" type="search" placeholder="输入选手姓名或编号搜索" autocomplete="off">
          <span v-if="playerSearch" class="search-result-count">{{ searchablePlayers.length }} 个结果</span>
        </label>
        <div v-if="playerSearch && searchablePlayers.length" class="player-match-list">
          <button
            v-for="player in searchablePlayers"
            :key="player.serial"
            type="button"
            :class="{ active: selectedPlayerSerial === player.serial }"
            @click="selectedPlayerSerial = player.serial; playerSearch = player.name"
          >
            <span>{{ player.name }}</span><small>{{ player.serial }} · {{ player.position }}</small>
          </button>
        </div>
        <p v-if="selected.state.historyComplete !== true" class="history-coverage-note">这份归档没有完整日志标记，较早的竞拍节点可能未被保存。</p>
        <div v-if="selectedPlayer" class="player-process-result">
          <div class="selected-player-title">
            <div><span>选手</span><strong>{{ selectedPlayer.name }}</strong><small>{{ selectedPlayer.serial }} · {{ selectedPlayer.position }}</small></div>
            <span class="round-count">{{ playerRounds.length }} 轮记录</span>
          </div>
          <p v-if="!playerRounds.length" class="process-empty">本场没有找到该选手的竞拍日志。</p>
          <div v-for="(round, roundIndex) in playerRounds" :key="`${selectedPlayer.serial}-${roundIndex}`" class="player-round">
            <h3><span>第 {{ roundIndex + 1 }} 轮</span><small>{{ round.stage }}</small></h3>
            <ol class="player-timeline">
              <li v-for="entry in round.entries" :key="entry.id" :class="entry.type">
                <span class="player-timeline-node" aria-hidden="true"></span>
                <time>{{ formatLogTime(entry.time) }}</time><span>{{ entry.text }}</span>
              </li>
            </ol>
          </div>
        </div>
        <p v-else-if="playerSearch && !searchablePlayers.length" class="process-empty">没有匹配到选手，请检查姓名或编号。</p>
        <p v-else class="process-empty process-placeholder">输入姓名或编号后，从候选结果中选择一名选手。</p>
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
                <li v-for="name in orderedTeam(captain.team)" :key="name">
                  <span class="position-tag" :style="{ '--position-color': positionFor(name) ? POSITION_COLORS[positionFor(name)!] : '#a59a8e' }">
                    {{ positionFor(name) ? POSITION_SHORT[positionFor(name)!] : '选手' }}
                  </span>
                  <span class="player-name">{{ name }}</span>
                  <span v-if="name !== captain.name && priceFor(name) !== null" class="player-price">{{ priceFor(name) }}w</span>
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
              <time>{{ formatLogTime(entry.time) }}</time>
              <span class="event-text">{{ entry.text }}</span>
            </li>
          </ol>
        </section>
      </div>

      <section class="unsold-section" aria-label="流拍名单">
        <header class="section-heading">
          <div>
            <p class="section-kicker">UNSOLD PLAYERS</p>
            <h2>流拍名单</h2>
          </div>
          <span class="section-count">{{ flowedPlayers.length }} 人</span>
        </header>
        <p v-if="!flowedPlayers.length" class="empty-unsold">本场没有流拍选手。</p>
        <div v-else class="unsold-position-grid">
          <article v-for="group in flowedGroups" :key="group.position" class="unsold-position-card">
            <header>
              <span class="position-tag" :style="{ '--position-color': POSITION_COLORS[group.position] }">{{ POSITION_SHORT[group.position] }}</span>
              <strong>{{ POSITION_NAMES[group.position] }}</strong>
              <small>{{ group.players.length }} 人</small>
            </header>
            <ul>
              <li v-for="player in group.players" :key="player.serial">
                <span class="unsold-player-name">{{ player.name }}</span>
                <span class="unsold-player-serial">{{ player.serial }}</span>
              </li>
            </ul>
          </article>
        </div>
      </section>
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

.player-process { margin: 0 0 1.4rem; padding: 1.15rem 1.25rem; border: 1px solid var(--line); border-radius: 13px; background: var(--surface); box-shadow: 0 4px 16px rgba(64, 45, 29, .035); }
.process-heading { display: flex; justify-content: space-between; align-items: start; gap: 1rem; }
.process-heading h2 { margin-top: .18rem; font: 600 1.35rem/1.25 Georgia, 'Songti SC', 'Noto Serif SC', serif; }
.process-heading p:last-child { margin-top: .35rem; color: var(--muted); font-size: .78rem; }
.process-player { padding: .4rem .65rem; border-radius: 999px; background: var(--terracotta-soft); color: var(--terracotta); font-size: .75rem; }
.player-search { display: flex; align-items: center; gap: .6rem; min-height: 2.8rem; margin-top: .85rem; padding: 0 .8rem; border: 1px solid var(--line); border-radius: 9px; background: #fffdfa; }
.player-search:focus-within { border-color: #c77b60; box-shadow: 0 0 0 3px rgba(184, 92, 63, .09); }
.search-icon { color: var(--terracotta); font-size: 1.25rem; line-height: 1; }
.player-search input { flex: 1; min-width: 0; height: 2.7rem; border: 0; outline: 0; color: var(--ink); background: transparent; font: 400 .84rem var(--font); }
.player-search input::placeholder { color: #a69b90; }
.search-result-count { color: var(--muted); font-size: .7rem; white-space: nowrap; }
.player-match-list { display: flex; flex-wrap: wrap; gap: .45rem; margin-top: .65rem; }
.player-match-list button { display: flex; align-items: center; gap: .5rem; padding: .45rem .65rem; border: 1px solid var(--line); border-radius: 8px; color: var(--ink); background: #fffdfa; cursor: pointer; font: inherit; }
.player-match-list button:hover, .player-match-list button.active { border-color: #c77b60; background: var(--terracotta-soft); }
.player-match-list small { color: var(--muted); font-size: .65rem; }
.player-process-result { margin-top: .85rem; border-top: 1px solid var(--line); }
.selected-player-title { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: .8rem 0 .35rem; }
.selected-player-title div { display: flex; align-items: baseline; flex-wrap: wrap; gap: .5rem; }
.selected-player-title div > span, .selected-player-title small { color: var(--muted); font-size: .7rem; }
.selected-player-title strong { font-size: .95rem; }
.round-count { color: var(--muted); font-size: .72rem; white-space: nowrap; }
.player-round { margin-top: .55rem; padding: .75rem .85rem; border: 1px solid #efe9e0; border-radius: 10px; background: #fdfbf7; }
.player-round h3 { display: flex; align-items: center; gap: .55rem; margin-bottom: .35rem; font-size: .78rem; }
.player-round h3 small { color: var(--muted); font-size: .65rem; font-weight: 500; }
.player-timeline { display: grid; gap: 0; margin: 0; padding: 0; list-style: none; }
.player-timeline li { display: grid; grid-template-columns: .7rem 3.3rem minmax(0, 1fr); align-items: baseline; gap: .5rem; padding: .42rem .15rem; border-bottom: 1px solid #f1ece5; color: #5b524a; font-size: .76rem; line-height: 1.5; overflow-wrap: anywhere; }
.player-timeline li:last-child { border-bottom: 0; }
.player-timeline time { color: #94887d; font: 600 .65rem/1.5 var(--font-display); font-variant-numeric: tabular-nums; }
.player-timeline-node { align-self: center; width: .42rem; height: .42rem; border: 1.5px solid #cfc5b9; border-radius: 50%; background: white; }
.player-timeline li.bid .player-timeline-node, .player-timeline li.buyout .player-timeline-node { border-color: #d59a59; background: #d59a59; }
.player-timeline li.win .player-timeline-node { border-color: #718f70; background: #718f70; }
.player-timeline li.warn .player-timeline-node { border-color: #c97b69; background: #c97b69; }
.history-coverage-note { margin-top: .7rem; padding: .55rem .75rem; border-radius: 8px; color: #8b6a37; background: #fbf2df; font-size: .7rem; }
.process-empty { margin-top: .7rem; padding: .7rem .8rem; border-radius: 8px; color: var(--muted); background: #f8f5ef; font-size: .76rem; }
.process-placeholder { border: 1px dashed var(--line); text-align: center; }
.unsold-section { margin-top: 1.4rem; padding: 1rem 1.1rem 1.1rem; border: 1px solid var(--line); border-radius: 13px; background: var(--surface); box-shadow: 0 4px 16px rgba(64, 45, 29, .035); }
.unsold-section .section-heading { margin-bottom: .75rem; }
.unsold-position-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 13rem), 1fr)); gap: .7rem; }
.unsold-position-card { min-width: 0; padding: .75rem .8rem; border: 1px solid var(--line); border-radius: 10px; background: #fffdfa; }
.unsold-position-card > header { display: flex; align-items: center; gap: .5rem; padding-bottom: .55rem; border-bottom: 1px solid #f0ebe4; }
.unsold-position-card > header strong { color: var(--ink); font-size: .78rem; }
.unsold-position-card > header small { margin-left: auto; color: var(--muted); font-size: .68rem; }
.unsold-position-card ul { display: grid; gap: .25rem; padding-top: .5rem; list-style: none; }
.unsold-position-card li { display: flex; justify-content: space-between; align-items: baseline; gap: .6rem; min-width: 0; padding: .3rem .1rem; }
.unsold-player-name { min-width: 0; color: #4d453e; font-size: .76rem; overflow-wrap: anywhere; }
.unsold-player-serial { flex: 0 0 auto; color: var(--muted); font-size: .64rem; }
.empty-unsold { padding: .75rem; border: 1px dashed var(--line); border-radius: 9px; color: var(--muted); font-size: .76rem; text-align: center; }
.history-page :is(.summary-item strong, .summary-date strong, .event-count, .section-count, .round-count, .search-result-count, .team-index, .funds strong, .player-price, .timeline time, .player-timeline time, .player-timeline-node, .unsold-player-serial) {
  font-family: var(--font);
  font-variant-numeric: lining-nums tabular-nums;
}
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
.player-name { min-width: 0; flex: 1; color: #4d453e; font-size: .75rem; line-height: 1.35; overflow-wrap: anywhere; }
.player-price { flex: 0 0 auto; color: var(--terracotta); font: 650 .72rem var(--font-display); font-variant-numeric: tabular-nums; }
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
  .player-process { padding: .9rem; }
  .player-timeline li { grid-template-columns: .6rem 2.8rem minmax(0, 1fr); gap: .35rem; font-size: .72rem; }
  .timeline { max-height: none; }
}
@media (max-width: 420px) {
  .head-actions { align-items: stretch; flex-direction: column; }
  .return-link { justify-content: center; }
  .timeline-entry { grid-template-columns: 3.25rem minmax(0, 1fr); gap: .35rem; }
}
</style>
