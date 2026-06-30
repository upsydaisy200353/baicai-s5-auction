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
</script>

<template>
  <div class="log-panel card">
    <h3 class="panel-title">拍卖日志</h3>
    <div class="log-list">
      <div
        v-for="entry in logs"
        :key="entry.id"
        class="log-entry"
        :class="typeClass[entry.type]"
      >
        <span class="log-time">{{ entry.time }}</span>
        <span class="log-text">{{ entry.text }}</span>
      </div>
      <div v-if="!logs.length" class="log-empty">等待拍卖开始…</div>
    </div>
  </div>
</template>

<style scoped>
.panel-title {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
  font-weight: 600;
}

.log-list {
  max-height: 360px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.log-entry {
  font-size: 0.8125rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  display: flex;
  gap: 0.5rem;
}

.log-time {
  color: var(--text-muted);
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

.log-bid { background: rgba(59, 130, 246, 0.08); color: #93c5fd; }
.log-buyout { background: var(--gold-dim); color: var(--gold); }
.log-win { background: var(--green-dim); color: var(--green); font-weight: 600; }
.log-phase { background: rgba(168, 85, 247, 0.1); color: var(--purple); }
.log-warn { color: var(--red); }

.log-empty {
  color: var(--text-muted);
  font-size: 0.8125rem;
  padding: 1rem;
  text-align: center;
}
</style>
