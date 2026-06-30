<script setup lang="ts">
import { POOL_LETTERS, POSITION_NAMES, POSITION_TO_LETTER } from '../constants'
import type { Captain, Position, RosterRow } from '../types'

defineProps<{
  rows: RosterRow[]
  currentPool?: Position | null
  highlightSerial?: string | null
}>()

function posLabel(position: Position) {
  const letter = POSITION_TO_LETTER[position]
  return `${letter}·${POSITION_NAMES[position]}`
}

function captainPosLabel(letter: Captain['poolLetter']) {
  return `${letter}·${POSITION_NAMES[POOL_LETTERS[letter]]}`
}
</script>

<template>
  <div class="player-table-wrap">
    <table class="player-table">
      <thead>
        <tr>
          <th>序号</th>
          <th>ID</th>
          <th>位置</th>
          <th>起拍价</th>
          <th>一口价</th>
          <th>成交价</th>
          <th>得主</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in rows"
          :key="row.kind === 'player' ? row.data.serial : `cap-${row.data.name}`"
          :class="{
            captain: row.kind === 'captain',
            sold: row.kind === 'player' && row.data.sold,
            current: row.kind === 'player' && row.data.serial === highlightSerial,
            'pool-match':
              row.kind === 'player' &&
              currentPool &&
              row.data.position === currentPool &&
              !row.data.sold,
          }"
        >
          <template v-if="row.kind === 'player'">
            <td>{{ row.data.serial }}</td>
            <td class="name">{{ row.data.name }}</td>
            <td><span class="badge badge-blue">{{ posLabel(row.data.position) }}</span></td>
            <td>{{ row.data.startPrice }}w</td>
            <td>{{ row.data.buyoutPrice }}w</td>
            <td>{{ row.data.finalPrice != null ? row.data.finalPrice + 'w' : '—' }}</td>
            <td>{{ row.data.winner ?? '—' }}</td>
          </template>
          <template v-else>
            <td><span class="badge badge-gold">队长</span></td>
            <td class="name captain-name">{{ row.data.name }}</td>
            <td><span class="badge badge-blue">{{ captainPosLabel(row.data.poolLetter) }}</span></td>
            <td>{{ row.data.rating }}</td>
            <td>—</td>
            <td>—</td>
            <td><span class="funds">{{ row.data.funds }}w</span></td>
          </template>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.player-table-wrap {
  overflow-x: auto;
  max-height: 420px;
  overflow-y: auto;
}

.player-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.player-table th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  color: var(--text-muted);
  font-weight: 600;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  background: var(--bg-card);
}

.player-table td {
  padding: 0.4rem 0.75rem;
  border-bottom: 1px solid rgba(45, 58, 79, 0.5);
}

.player-table .name {
  font-weight: 600;
}

.player-table tr.captain {
  background: rgba(245, 158, 11, 0.06);
}

.player-table tr.captain .captain-name {
  color: var(--gold);
}

.player-table tr.captain .funds {
  color: var(--gold);
  font-weight: 600;
}

.player-table tr.sold {
  opacity: 0.55;
}

.player-table tr.current {
  background: var(--gold-dim);
}

.player-table tr.current td:first-child {
  border-left: 3px solid var(--gold);
}

.player-table tr.pool-match:not(.sold):not(.current) {
  background: rgba(59, 130, 246, 0.06);
}
</style>
