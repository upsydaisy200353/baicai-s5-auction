<script setup lang="ts">
import { computed, ref } from 'vue'
import { POSITION_COLORS } from '../constants'
import type { Position } from '../types'

const props = withDefaults(
  defineProps<{
    name: string
    serial?: string
    avatar?: string | null
    position?: Position | null
    size?: 'sm' | 'md' | 'lg' | 'xl'
  }>(),
  {
    size: 'md',
  },
)

const failed = ref(false)

const initials = computed(() => props.name.slice(0, 1).toUpperCase())

const accent = computed(() =>
  props.position ? POSITION_COLORS[props.position] : 'var(--accent)',
)

function onError() {
  failed.value = true
}
</script>

<template>
  <div
    class="player-avatar"
    :class="[`size-${size}`, { 'has-photo': avatar && !failed }]"
    :style="{ '--accent': accent }"
    :title="name"
  >
    <img
      v-if="avatar && !failed"
      :src="avatar"
      :alt="name"
      class="avatar-img"
      loading="lazy"
      @error="onError"
    />
    <span v-else class="avatar-fallback">
      <span class="avatar-initial">{{ initials }}</span>
      <small v-if="serial" class="avatar-serial">{{ serial }}</small>
    </span>
  </div>
</template>

<style scoped>
.player-avatar {
  position: relative;
  flex-shrink: 0;
  border-radius: 14px;
  overflow: hidden;
  background: linear-gradient(145deg, color-mix(in srgb, var(--accent) 75%, #000), var(--accent));
  border: 2px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 6px 20px color-mix(in srgb, var(--accent) 28%, transparent);
}

.player-avatar.has-photo {
  border-color: rgba(255, 255, 255, 0.18);
}

.size-sm {
  width: 36px;
  height: 36px;
  border-radius: 10px;
}

.size-md {
  width: 48px;
  height: 48px;
}

.size-lg {
  width: 72px;
  height: 72px;
  border-radius: 16px;
}

.size-xl {
  width: 96px;
  height: 96px;
  border-radius: 18px;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center top;
  display: block;
}

.avatar-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-family: var(--font-display);
  font-weight: 800;
}

.size-sm .avatar-initial {
  font-size: 0.95rem;
}

.size-md .avatar-initial {
  font-size: 1.1rem;
}

.size-lg .avatar-initial {
  font-size: 1.35rem;
}

.size-xl .avatar-initial {
  font-size: 1.75rem;
}

.avatar-serial {
  font-size: 0.55rem;
  opacity: 0.85;
  margin-top: 0.1rem;
}

.size-sm .avatar-serial {
  display: none;
}
</style>
