<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { deleteFeedback, fetchFeedbackList, type FeedbackItem } from '../api/feedback'
import { playSound, unlockAudio } from '../lib/soundEngine'

const items = ref<FeedbackItem[]>([])
const loading = ref(true)
const error = ref('')
const deletingId = ref<number | null>(null)

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    items.value = await fetchFeedbackList()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(refresh)

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleString('zh-CN', { hour12: false })
  } catch {
    return iso
  }
}

async function onDelete(id: number) {
  if (!confirm('确认删除这条反馈？')) return
  deletingId.value = id
  void unlockAudio()
  playSound('uiClick')
  try {
    await deleteFeedback(id)
    items.value = items.value.filter((x) => x.id !== id)
    playSound('uiConfirm')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '删除失败'
    playSound('uiError')
  } finally {
    deletingId.value = null
  }
}
</script>

<template>
  <div class="feedback-admin">
    <header class="head card">
      <div>
        <p class="eyebrow">ADMIN · FEEDBACK</p>
        <h1 class="title">用户反馈</h1>
        <p class="sub">测试用户提交的修改意见，共 {{ items.length }} 条</p>
      </div>
      <button class="btn-ghost" :disabled="loading" @click="refresh">刷新</button>
    </header>

    <p v-if="error" class="banner error">{{ error }}</p>
    <p v-else-if="loading" class="banner info">加载反馈…</p>
    <p v-else-if="!items.length" class="banner info">暂无反馈</p>

    <ul v-else class="list">
      <li v-for="item in items" :key="item.id" class="item card">
        <div class="item-head">
          <span class="author">{{ item.authorName || '匿名用户' }}</span>
          <span class="time">{{ formatTime(item.createdAt) }}</span>
        </div>
        <p class="content">{{ item.content }}</p>
        <button
          class="btn-ghost btn-del"
          :disabled="deletingId === item.id"
          @click="onDelete(item.id)"
        >
          {{ deletingId === item.id ? '删除中…' : '删除' }}
        </button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.feedback-admin {
  width: 100%;
}

.head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.15rem 1.25rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.eyebrow {
  font-family: var(--font-display);
  font-size: 0.65rem;
  letter-spacing: 0.14em;
  color: var(--gold);
}

.title {
  font-family: var(--font-display);
  font-size: 1.45rem;
  font-weight: 800;
}

.sub {
  margin-top: 0.25rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.banner {
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.banner.info {
  background: rgba(56, 189, 248, 0.08);
  color: #7dd3fc;
  border: 1px solid rgba(56, 189, 248, 0.2);
}

.banner.error {
  background: var(--red-dim);
  color: var(--red);
}

.list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.item {
  padding: 1rem 1.15rem;
  position: relative;
}

.item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.55rem;
  flex-wrap: wrap;
}

.author {
  font-weight: 700;
  color: var(--cabbage);
}

.time {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.content {
  white-space: pre-wrap;
  line-height: 1.65;
  font-size: 0.9375rem;
  margin-bottom: 0.75rem;
}

.btn-del {
  font-size: 0.78rem;
  padding: 0.3rem 0.7rem;
  color: var(--red);
  border-color: rgba(248, 113, 113, 0.25);
}
</style>
