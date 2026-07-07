import { ref, watch } from 'vue'

const STORAGE_KEY = 'baicai-auction-sound-muted'

const muted = ref(localStorage.getItem(STORAGE_KEY) === '1')

watch(muted, (value) => {
  localStorage.setItem(STORAGE_KEY, value ? '1' : '0')
})

export function useSoundSettings() {
  function toggleMute() {
    muted.value = !muted.value
  }

  function unmute() {
    muted.value = false
  }

  return { muted, toggleMute, unmute }
}

export function isSoundMuted() {
  return muted.value
}
