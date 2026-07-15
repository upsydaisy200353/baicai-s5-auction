import { apiRequest } from './client'

export interface FeedbackItem {
  id: number
  authorName: string | null
  content: string
  createdAt: string
}

export function submitFeedback(payload: { content: string; authorName?: string | null }) {
  return fetch('/api/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      content: payload.content,
      authorName: payload.authorName?.trim() || null,
    }),
  }).then(async (res) => {
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail ?? `HTTP ${res.status}`)
    }
    return res.json() as Promise<FeedbackItem>
  })
}

export function fetchFeedbackList() {
  return apiRequest<FeedbackItem[]>('/feedback')
}

export function deleteFeedback(id: number) {
  return apiRequest<{ ok: boolean }>(`/feedback/${id}`, { method: 'DELETE' })
}
