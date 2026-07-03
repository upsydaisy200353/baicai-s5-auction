<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { fetchSpectatorState, type ServerAuctionState } from '../api/auction'
import CeremonyOverlay from '../components/CeremonyOverlay.vue'
import SpectatorBoard from '../components/SpectatorBoard.vue'

const state = ref<ServerAuctionState | null>(null)
const error = ref('')
let pollTimer: ReturnType<typeof setInterval> | null = null

const overlayPhases = ['intro', 'pool_draw', 'winner_reveal', 'finished']

async function refresh() {
  try {
    state.value = await fetchSpectatorState()
    error.value = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : '同步失败'
  }
}

onMounted(async () => {
  await refresh()
  pollTimer = setInterval(refresh, 1200)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="spectator-view">
    <div v-if="error" class="banner error">{{ error }}</div>

    <template v-if="state">
      <CeremonyOverlay
        v-if="overlayPhases.includes(state.phase)"
        :phase="state.phase"
        :captains="state.captains"
        :current-pool="state.currentPool"
        :pool-order="state.poolOrder"
        :draw-candidates="state.drawCandidates"
        :last-result="state.lastResult"
      />

      <SpectatorBoard
        v-if="state.phase !== 'idle'"
        :phase="state.phase"
        :captains="state.captains"
        :current-pool="state.currentPool"
        :current-player="state.currentPlayer"
        :open-bid="state.openBid"
        :pool-order="state.poolOrder"
      />

      <div v-else class="idle card">
        <img src="/logo.svg" alt="" class="idle-logo" />
        <h1>观战大屏</h1>
        <p>等待管理员开始仪式…</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.spectator-view {
  width: 100%;
  min-height: 100vh;
  padding: 1rem;
}

.banner.error {
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  margin-bottom: 1rem;
  background: var(--red-dim);
  color: var(--red);
}

.idle {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  gap: 0.5rem;
  color: var(--text-muted);
}

.idle-logo {
  width: 72px;
  opacity: 0.8;
}

.idle h1 {
  font-family: var(--font-display);
  font-size: 1.5rem;
  color: var(--text);
}
</style>
