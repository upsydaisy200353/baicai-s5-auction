<script setup lang="ts">
import { computed, ref } from 'vue'
import { POSITION_COLORS } from '../constants'
import type { Position } from '../types'

const DEFAULT_AVATARS = [
  '/splash/Aatrox_暗裔剑魔.jpg',
  '/splash/Ahri_九尾妖狐.jpg',
  '/splash/Garen_德玛西亚之力.jpg',
  '/splash/LeeSin_盲僧.jpg',
  '/splash/Yasuo_疾风剑豪.jpg',
  '/splash/Jinx_暴走萝莉.jpg',
  '/splash/Ezreal_探险家.jpg',
  '/splash/Lux_光辉女郎.jpg',
  '/splash/Darius_诺克萨斯之手.jpg',
  '/splash/Jax_武器大师.jpg',
  '/splash/Zed_影流之主.jpg',
  '/splash/Katarina_不祥之刃.jpg',
  '/splash/Caitlyn_皮城女警.jpg',
  '/splash/Vayne_暗夜猎手.jpg',
  '/splash/Sett_腕豪.jpg',
  '/splash/Kayn_影流之镰.jpg',
  '/splash/Kaisa_虚空之女.jpg',
  '/splash/Samira_沙漠玫瑰.jpg',
  '/splash/Fiora_无双剑姬.jpg',
  '/splash/Camille_青钢影.jpg',
]

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

const accent = computed(() =>
  props.position ? POSITION_COLORS[props.position] : 'var(--accent)',
)

const defaultAvatar = computed(() => {
  let hash = 0
  for (let i = 0; i < props.name.length; i++) {
    hash = props.name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return DEFAULT_AVATARS[Math.abs(hash) % DEFAULT_AVATARS.length]
})

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
    <img
      v-else
      :src="defaultAvatar"
      :alt="name"
      class="avatar-img"
      loading="lazy"
    />
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
