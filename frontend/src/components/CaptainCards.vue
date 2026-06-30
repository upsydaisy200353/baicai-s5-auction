<script setup lang="ts">
import { computed } from 'vue'
import type { Captain } from '../types'

const props = defineProps<{
  captains: Captain[]
  activeName?: string | null
}>()

const sorted = computed(() =>
  [...props.captains].sort((a, b) => b.rating - a.rating),
)
</script>

<template>
  <div class="captain-grid">
    <div
      v-for="cap in sorted"
      :key="cap.name"
      class="captain-card card"
      :class="{ active: cap.name === activeName, broke: cap.funds <= 0 }"
    >
      <div class="cap-header">
        <span class="cap-name">{{ cap.name }}</span>
        <span class="badge badge-blue">实力 {{ cap.rating }}</span>
      </div>
      <div class="cap-funds">
        <span class="label">剩余资金</span>
        <span class="amount">{{ cap.funds }}<small>w</small></span>
      </div>
      <div v-if="cap.team.length" class="cap-team">
        <span class="label">队员</span>
        <div class="team-tags">
          <span v-for="t in cap.team" :key="t" class="team-tag">{{ t }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.captain-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem;
}

.captain-card {
  transition: border-color 0.2s, box-shadow 0.2s;
}

.captain-card.active {
  border-color: var(--gold);
  box-shadow: 0 0 20px var(--gold-dim);
}

.captain-card.broke {
  opacity: 0.5;
}

.cap-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.cap-name {
  font-weight: 700;
  font-size: 1rem;
}

.cap-funds {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.5rem;
}

.label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.amount {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--gold);
}

.amount small {
  font-size: 0.75rem;
  opacity: 0.7;
}

.cap-team .team-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.25rem;
}

.team-tag {
  font-size: 0.7rem;
  background: var(--bg-hover);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  color: var(--text-muted);
}
</style>
