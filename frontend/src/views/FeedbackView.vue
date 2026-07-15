<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { submitFeedback } from '../api/feedback'
import { playSound, unlockAudio } from '../lib/soundEngine'
import { useAuth } from '../stores/auth'

const { user } = useAuth()

const authorName = ref('')
const anonymous = ref(false)
const content = ref('')
const submitting = ref(false)
const error = ref('')
const success = ref(false)

onMounted(() => {
  if (user.value?.displayName) {
    authorName.value = user.value.displayName
  }
})

async function onSubmit() {
  error.value = ''
  success.value = false
  const text = content.value.trim()
  if (!text) {
    error.value = '请填写反馈内容'
    playSound('uiError')
    return
  }
  submitting.value = true
  void unlockAudio()
  playSound('uiClick')
  try {
    await submitFeedback({
      content: text,
      authorName: anonymous.value ? null : authorName.value.trim() || null,
    })
    playSound('uiConfirm')
    success.value = true
    content.value = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : '提交失败'
    playSound('uiError')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="feedback-page">
    <div class="feedback-card card fade-in">
      <p class="eyebrow">FEEDBACK</p>
      <h1 class="title">留下修改意见</h1>
      <p class="sub">测试过程中发现的问题、希望改进的地方都可以写在这里。姓名可选。</p>

      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span class="label-row">
            <span>姓名（可选）</span>
            <label class="anon-toggle">
              <input v-model="anonymous" type="checkbox" />
              匿名提交
            </label>
          </span>
          <input
            v-model="authorName"
            type="text"
            class="input"
            maxlength="64"
            placeholder="可留空或勾选匿名"
            :disabled="anonymous || submitting"
          />
        </label>

        <label class="field">
          <span>意见内容</span>
          <textarea
            v-model="content"
            class="textarea"
            rows="6"
            maxlength="2000"
            placeholder="例如：倒计时音效太急、希望增加某某按钮…"
            :disabled="submitting"
            required
          />
          <span class="char-count">{{ content.length }} / 2000</span>
        </label>

        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="ok">感谢反馈，已保存！</p>

        <div class="actions">
          <button type="submit" class="btn-primary" :disabled="submitting">
            {{ submitting ? '提交中…' : '提交反馈' }}
          </button>
          <RouterLink to="/login" class="btn-ghost">返回登录</RouterLink>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.feedback-page {
  max-width: 560px;
  margin: 0 auto;
  padding: 0.5rem 0 2rem;
}

.feedback-card {
  padding: 1.75rem 1.5rem;
}

.eyebrow {
  font-family: var(--font-display);
  font-size: 0.68rem;
  letter-spacing: 0.18em;
  color: var(--cabbage);
  margin-bottom: 0.45rem;
}

.title {
  font-family: var(--font-display);
  font-size: 1.55rem;
  font-weight: 800;
  margin-bottom: 0.4rem;
}

.sub {
  color: var(--text-muted);
  font-size: 0.875rem;
  line-height: 1.6;
  margin-bottom: 1.35rem;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.anon-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 0.78rem;
}

.input,
.textarea {
  width: 100%;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text);
  padding: 0.65rem 0.75rem;
  font-size: 0.9375rem;
  font-family: inherit;
  resize: vertical;
}

.input:disabled,
.textarea:disabled {
  opacity: 0.55;
}

.textarea:focus,
.input:focus {
  outline: none;
  border-color: rgba(74, 222, 128, 0.4);
}

.char-count {
  align-self: flex-end;
  font-size: 0.72rem;
  color: var(--text-muted);
}

.error {
  color: var(--red);
  font-size: 0.8125rem;
}

.ok {
  color: var(--cabbage);
  font-size: 0.8125rem;
}

.actions {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
  margin-top: 0.25rem;
}
</style>
