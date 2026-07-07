<script setup lang="ts">
import { unlockAudio } from '../lib/soundEngine'
import { useSoundSettings } from '../stores/sound'

const { muted, toggleMute } = useSoundSettings()

async function onToggle() {
  toggleMute()
  if (!muted.value) await unlockAudio()
}
</script>

<template>
  <button
    type="button"
    class="sound-toggle"
    :class="{ muted }"
    :aria-label="muted ? '开启音效' : '关闭音效'"
    :title="muted ? '开启音效' : '关闭音效'"
    @click="onToggle"
  >
    <span class="sound-icon" aria-hidden="true">{{ muted ? '🔇' : '🔊' }}</span>
    <span class="sound-label">{{ muted ? '音效关' : '音效开' }}</span>
  </button>
</template>

<style scoped>
.sound-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-muted);
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
}

.sound-toggle:hover {
  color: var(--text);
  border-color: rgba(74, 222, 128, 0.35);
  background: rgba(74, 222, 128, 0.06);
}

.sound-toggle.muted {
  opacity: 0.75;
}

.sound-icon {
  font-size: 0.95rem;
  line-height: 1;
}

.sound-label {
  letter-spacing: 0.02em;
}
</style>
