<script setup lang="ts">
import type { LogEntry } from '../types'

defineProps<{ logs: LogEntry[] }>()

const typeClass: Record<LogEntry['type'], string> = {
  info: '',
  bid: 'log-bid',
  buyout: 'log-buyout',
  win: 'log-win',
  phase: 'log-phase',
  warn: 'log-warn',
}

const typeIcon: Record<LogEntry['type'], string> = {
  info: '·',
  bid: '↑',
  buyout: '★',
  win: '✓',
  phase: '◆',
  warn: '!',
}
</script>

<template>
  <div class="log-panel card">
    <div class="panel-head">
      <h3 class="panel-title">拍卖日志</h3>
      <span class="live-badge">实时</span>
    </div>
    <div class="log-list">
      <div
        v-for="(entry, i) in logs"
        :key="entry.id"
        class="log-entry"
        :class="typeClass[entry.type]"
        :style="{ '--log-i': i }"
      >
        <span class="log-icon">{{ typeIcon[entry.type] }}</span>
        <span class="log-time">{{ entry.time }}</span>
        <span class="log-text">{{ entry.text }}</span>
      </div>
      <div v-if="!logs.length" class="log-empty">
        <span class="empty-icon">📋</span>
        等待拍卖开始…
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.panel-title {
  font-family: var(--font-display);
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.live-badge {
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: var(--cabbage);
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  background: var(--cabbage-dim);
  border: 1px solid rgba(74, 222, 128, 0.25);
}

.log-list {
  max-height: 360px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.log-entry {
  font-size: 0.8rem;
  padding: 0.4rem 0.55rem;
  border-radius: 8px;
  display: grid;
  grid-template-columns: auto auto 1fr;
  gap: 0.45rem;
  align-items: start;
  animation: fadeUp 0.3s ease both;
  animation-delay: calc(var(--log-i) * 0.02s);
  border-left: 2px solid transparent;
}

.log-icon {
  font-size: 0.65rem;
  opacity: 0.7;
  width: 0.75rem;
  text-align: center;
  padding-top: 0.1rem;
}

.log-time {
  color: var(--text-muted);
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
  font-size: 0.72rem;
  min-width: 3.2rem;
}

.log-bid {
  background: rgba(56, 189, 248, 0.08);
  color: #7dd3fc;
  border-left-color: var(--accent);
}

.log-buyout {
  background: var(--gold-dim);
  color: var(--gold);
  border-left-color: var(--gold);
}

.log-win {
  background: var(--green-dim);
  color: var(--green);
  font-weight: 600;
  border-left-color: var(--green);
}

.log-phase {
  background: rgba(192, 132, 252, 0.1);
  color: var(--purple);
  border-left-color: var(--purple);
}

.log-warn {
  color: var(--red);
  border-left-color: var(--red);
}

.log-empty {
  color: var(--text-muted);
  font-size: 0.8125rem;
  padding: 2rem 1rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.empty-icon {
  font-size: 1.5rem;
  opacity: 0.5;
}
</style>
